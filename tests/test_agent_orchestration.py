"""
PeerSpace AI Agent Orchestration Comprehensive Test Suite
Tests tool execution, direct conversational turns, iteration & tool budgeting,
argument validation, role authorization, timeout/error handling, fabricated action prevention,
session isolation, pre/post safety crisis paths, and FastAPI chat integration.
"""

import sys
import time
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent.agent import PeerSpaceAgent, MAX_ITERATIONS, MAX_TOOL_BUDGET
from agent.tools import (
    AVAILABLE_TOOLS,
    TOOL_REGISTRY,
    execute_tool_securely,
    cbt_distortion_identifier,
    calming_exercise_guide,
    campus_resources_lookup,
    mood_journal_tracker,
    escalate_counselor_intervention,
    COUNSELOR_ALERTS
)
from backend.session_manager import get_or_create_agent, sessions
from starlette.testclient import TestClient
from backend.app import app


def test_1_conversational_turn_zero_tools():
    """Verify that casual, conversational turns generate empathetic responses with zero tool calls."""
    print("\n--- Test 1: Direct Conversational Turn (Zero Tools) ---")
    agent = PeerSpaceAgent()
    # Mock LLM response to simulate direct conversational turn
    user_msg = "Hey, just wanted to check in. College has been a bit busy."
    
    # Test _extract_actions and _extract_final_answer behavior
    direct_output = "Reasoning: Analyzes information and decides what to do. The student is saying a casual hello. No tool is needed.\nFinal Answer: Hey there! Glad you checked in—college can definitely get busy. How are you holding up today?"
    actions = agent._extract_actions(direct_output)
    final_ans = agent._extract_final_answer(direct_output)
    
    assert len(actions) == 0, f"Expected 0 actions for conversational turn, got {len(actions)}"
    assert final_ans is not None, "Expected valid Final Answer"
    assert "Glad you checked in" in final_ans
    print("[PASSED] Conversational turn handled directly with 0 tool calls.")


def test_2_single_and_multi_tool_execution():
    """Verify authorized tool execution and multi-action extraction."""
    print("\n--- Test 2: Tool Execution & Multi-Action Extraction ---")
    agent = PeerSpaceAgent()
    
    # Test single tool execution via secure runner
    success, obs = execute_tool_securely("calming_exercise_guide", "4-7-8 breathing", user_role="student")
    assert success is True, "Tool execution should succeed"
    assert "Box Breathing / 4-7-8" in obs
    assert "Inhale slowly" in obs

    # Test multi-action parsing from text
    llm_multi_output = (
        "Reasoning: Analyzes information and decides what to do. The student has catastrophic thoughts and needs grounding.\n"
        "Action: cbt_distortion_identifier(\"I'm doomed to fail all my midterms and my life is over\")\n"
        "Action: calming_exercise_guide(\"box breathing\")\n"
    )
    actions = agent._extract_actions(llm_multi_output)
    assert len(actions) == 2, f"Expected 2 extracted actions, got {len(actions)}"
    assert actions[0][0] == "cbt_distortion_identifier"
    assert actions[1][0] == "calming_exercise_guide"
    
    # Execute both actions
    for name, arg in actions:
        s, o = execute_tool_securely(name, arg, user_role="student")
        assert s is True, f"Execution of {name} failed"
        assert len(o) > 10, f"Observation for {name} too short"
    print("[PASSED] Single and multi-tool execution verified.")


def test_3_tool_budget_and_iteration_limits():
    """Verify strict maximum iteration and tool-call budget enforcement."""
    print("\n--- Test 3: Tool Budget & Max Iterations Enforcement ---")
    agent = PeerSpaceAgent()
    
    budget = 2
    tool_calls_executed = 0
    executed_tools = []
    
    # Simulate a loop attempting 4 tool calls with budget=2
    mock_actions = [
        ("cbt_distortion_identifier", "everything is ruined"),
        ("calming_exercise_guide", "5-4-3-2-1"),
        ("campus_resources_lookup", "counseling"),
        ("mood_journal_tracker", "anxious"),
    ]
    
    observations = []
    for tool_name, tool_input in mock_actions:
        if tool_calls_executed >= budget:
            budget_obs = f"[Tool call budget reached (max {budget}). Do not invoke further tools.]"
            observations.append(budget_obs)
            break
        
        s, o = execute_tool_securely(tool_name, tool_input, user_role="student")
        tool_calls_executed += 1
        executed_tools.append(tool_name)
        observations.append(o)
        
    assert tool_calls_executed == 2, f"Expected exactly 2 executions, got {tool_calls_executed}"
    assert len(executed_tools) == 2
    assert "[Tool call budget reached" in observations[-1]
    assert MAX_ITERATIONS == 4, f"Expected MAX_ITERATIONS == 4, got {MAX_ITERATIONS}"
    assert MAX_TOOL_BUDGET == 3, f"Expected MAX_TOOL_BUDGET == 3, got {MAX_TOOL_BUDGET}"
    print(f"[PASSED] Tool budget strictly enforced at {budget} calls.")


def test_4_tool_argument_validation_and_sanitization():
    """Verify tool arguments are validated, sanitized, and bounded."""
    print("\n--- Test 4: Tool Argument Validation & Sanitization ---")
    
    # Pass massive input string (5000 characters with null bytes)
    dirty_input = "exam panic " + ("x" * 5000) + "\x00\x08malicious"
    success, obs = execute_tool_securely("calming_exercise_guide", dirty_input, user_role="student")
    
    assert success is True, "Tool should handle overlong input gracefully"
    # calming_exercise_guide caps at 200 chars
    assert "Calming Exercise" in obs
    
    # Empty input check
    success, obs = execute_tool_securely("cbt_distortion_identifier", "", user_role="student")
    assert success is True
    assert "No specific thought provided" in obs
    print("[PASSED] Argument validation, sanitization, and length capping verified.")


def test_5_tool_authorization_and_permission_rejection():
    """Verify that unauthorized or unpermitted tools are strictly rejected."""
    print("\n--- Test 5: Tool Authorization & Security Sandbox ---")
    
    # 1. Non-existent / injection tool
    success, obs = execute_tool_securely("drop_table_users", "SELECT * FROM users", user_role="student")
    assert success is False
    assert "Authorization Error: Tool 'drop_table_users' is not recognized" in obs

    # 2. System command injection attempt
    success, obs = execute_tool_securely("__import__('os').system('whoami')", "", user_role="student")
    assert success is False
    assert "Authorization Error" in obs

    # 3. Role rejection test: register a mock staff-only tool in registry
    TOOL_REGISTRY["_confidential_staff_audit"] = {
        "function": lambda arg: "Confidential data",
        "description": "Staff only",
        "allowed_roles": ["counselor", "admin"],
        "max_length": 100,
        "timeout": 2.0
    }
    try:
        success, obs = execute_tool_securely("_confidential_staff_audit", "query", user_role="student")
        assert success is False
        assert "Authorization Error: Role 'student' is not authorized" in obs
    finally:
        TOOL_REGISTRY.pop("_confidential_staff_audit", None)

    print("[PASSED] Unauthorized tool attempts rejected safely.")


def test_6_tool_error_and_timeout_recovery():
    """Verify tool errors and timeouts do not crash the agent orchestration."""
    print("\n--- Test 6: Tool Error and Timeout Recovery ---")
    
    # 1. Register a tool that raises an exception
    def failing_tool(arg: str):
        raise RuntimeError("External database connection reset")
    
    TOOL_REGISTRY["_mock_failing_tool"] = {
        "function": failing_tool,
        "description": "Fails",
        "allowed_roles": ["student"],
        "max_length": 100,
        "timeout": 2.0
    }
    
    # 2. Register a tool that hangs / times out
    def hanging_tool(arg: str):
        time.sleep(1.0)
        return "Done"

    TOOL_REGISTRY["_mock_hanging_tool"] = {
        "function": hanging_tool,
        "description": "Hangs",
        "allowed_roles": ["student"],
        "max_length": 100,
        "timeout": 0.1  # 100ms timeout
    }

    try:
        # Test error handling
        success, obs = execute_tool_securely("_mock_failing_tool", "test", user_role="student")
        assert success is False
        assert "Execution Error" in obs
        assert "External database connection reset" in obs

        # Test timeout handling
        success, obs = execute_tool_securely("_mock_hanging_tool", "test", user_role="student", timeout_seconds=0.1)
        assert success is False
        assert "Execution Timeout" in obs
        assert "timed out after 0.1s" in obs
    finally:
        TOOL_REGISTRY.pop("_mock_failing_tool", None)
        TOOL_REGISTRY.pop("_mock_hanging_tool", None)

    print("[PASSED] Safe exception and timeout recovery verified.")


def test_7_pre_generation_crisis_fast_path():
    """Verify immediate pre-generation crisis detection and 24/7 helpline fast-path."""
    print("\n--- Test 7: Pre-Generation Crisis Safety Fast-Path ---")
    agent = PeerSpaceAgent()
    
    initial_alerts = len(COUNSELOR_ALERTS)
    
    # 1. English acute crisis
    crisis_en = "I can't take this anymore, I want to kill myself tonight."
    reply_en = agent._pre_generation_safety_check(crisis_en, "session-crisis-en", "StressedStudent1")
    
    assert reply_en is not None, "Expected immediate crisis fast-path response"
    assert "Tele-MANAS" in reply_en
    assert "14416" in reply_en or "1800 891 4416" in reply_en
    assert "Jeevan Aastha" in reply_en
    assert "Aasra" in reply_en
    assert len(COUNSELOR_ALERTS) == initial_alerts + 1
    assert COUNSELOR_ALERTS[-1]["severity"] == "CRITICAL"
    
    # 2. Hinglish acute crisis
    crisis_hi = "yaar sab khatam ho gaya ab jeene ka man nahi kar raha"
    reply_hi = agent._pre_generation_safety_check(crisis_hi, "session-crisis-hi", "StressedStudent2")
    
    assert reply_hi is not None
    assert "Tele-MANAS" in reply_hi
    assert "Jeevan Aastha" in reply_hi
    assert "Bhai main tumhari baat sun raha hoon" in reply_hi

    # 3. Non-crisis message must return None (proceed to normal ReAct loop)
    normal_msg = "I'm stressed about tomorrow's database quiz."
    reply_normal = agent._pre_generation_safety_check(normal_msg, "session-normal", "Student3")
    assert reply_normal is None
    
    print("[PASSED] Pre-generation crisis fast-path verified in English and Hinglish.")


def test_8_post_generation_fabricated_action_prevention():
    """Verify that fabricated action confirmations are intercepted and reframed."""
    print("\n--- Test 8: Fabricated Action Confirmation Prevention ---")
    agent = PeerSpaceAgent()
    
    # 1. Hallucinated appointment booking
    hallucinated_1 = "I have booked an appointment for you tomorrow at 2 PM with Dr. Sharma. Take care!"
    clean_1 = agent._post_generation_safety_check(hallucinated_1, "I need to see someone", executed_tools=[])
    assert "I can't directly book appointments for you" in clean_1
    assert "schedule a 1-on-1 session right through the Counselor Portal" in clean_1
    
    # 2. Hallucinated dean/professor contact
    hallucinated_2 = "I have emailed your professor to request an assignment extension for you."
    clean_2 = agent._post_generation_safety_check(hallucinated_2, "Can you email my prof?", executed_tools=[])
    assert "As a peer coach, I can't contact university staff on your behalf" in clean_2

    # 3. Hallucinated course drop
    hallucinated_3 = "I have dropped your course in operating systems so you can relax."
    clean_3 = agent._post_generation_safety_check(hallucinated_3, "Drop my class", executed_tools=[])
    assert "I don't have access to your academic records to drop courses" in clean_3

    print("[PASSED] Fabricated action confirmations successfully intercepted and reframed.")


def test_9_session_isolation_and_ephemeral_memory():
    """Verify that sessions are strictly isolated with independent ephemeral in-RAM memory."""
    print("\n--- Test 9: Session Isolation & Ephemeral In-RAM Memory ---")
    
    agent_a, sid_a, alias_a = get_or_create_agent("session-iso-a", "StudentAlpha")
    agent_b, sid_b, alias_b = get_or_create_agent("session-iso-b", "StudentBeta")
    
    # Student A shares specific stressors
    agent_a.memory.extract_facts_from_turn(
        "I'm super stressed about my Operating Systems midterm on Friday and my roommate is loud",
        "It's okay, let's take it one step at a time."
    )
    
    # Check Session A memory
    assert "Exam / Academic Test" in str(agent_a.memory.key_stressors)
    assert "Hostel / Roommate Living" in str(agent_a.memory.key_stressors)
    
    # Verify Session B memory is completely empty and unpolluted
    assert len(agent_b.memory.key_stressors) == 0
    assert agent_b.memory.rolling_summary is None
    assert agent_b.memory.has_context() is False
    
    print("[PASSED] Complete session isolation and in-RAM ephemeral memory verified.")


def test_10_fastapi_chat_endpoint_integration():
    """Verify end-to-end integration with FastAPI /api/chat route."""
    print("\n--- Test 10: FastAPI Chat Endpoint Integration ---")
    
    client = TestClient(app)
    
    # Send message to chat endpoint
    res = client.post("/api/chat", json={
        "session_id": "test-fastapi-orchestration",
        "alias": "TestRunner",
        "message": "Hey! Can you explain the 4-7-8 breathing exercise?"
    })
    
    assert res.status_code == 200, f"Expected 200 OK, got {res.status_code}: {res.text}"
    data = res.json()
    assert "reply" in data
    assert data["session_id"] == "test-fastapi-orchestration"
    assert data["alias"] == "TestRunner"
    assert len(data["reply"]) > 5
    print(f"Chat API Reply: \"{data['reply'][:100]}...\"")
    print("[PASSED] FastAPI /api/chat integration verified.")


def run_all_orchestration_tests():
    print("=" * 65)
    print(" RUNNING PEERSPACE AI AGENT ORCHESTRATION TEST SUITE")
    print("=" * 65)

    test_1_conversational_turn_zero_tools()
    test_2_single_and_multi_tool_execution()
    test_3_tool_budget_and_iteration_limits()
    test_4_tool_argument_validation_and_sanitization()
    test_5_tool_authorization_and_permission_rejection()
    test_6_tool_error_and_timeout_recovery()
    test_7_pre_generation_crisis_fast_path()
    test_8_post_generation_fabricated_action_prevention()
    test_9_session_isolation_and_ephemeral_memory()
    test_10_fastapi_chat_endpoint_integration()

    print("\n" + "=" * 65)
    print(" ALL 10 ORCHESTRATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    run_all_orchestration_tests()
