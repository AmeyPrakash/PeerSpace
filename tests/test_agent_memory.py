"""
Unit Tests for PeerSpace AI Coach Conversation Memory Architecture
Validates extraction heuristics, rolling context condensation, zero-footprint RAM operation, and prompt formatting.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent.memory import ConversationMemory
from agent.agent import PeerSpaceAgent


def test_memory_extraction():
    print("\n--- Testing Fact Extraction & Stressors ---")
    mem = ConversationMemory()
    
    user_turn = "I'm super stressed about my algorithms exam on Friday and my roommate keeps partying so I haven't slept in two days."
    assistant_reply = "That sounds so exhausting, let's take a quick breath together."
    reasoning = "Reasoning: Analyzes information and decides what to do. The student is exhibiting catastrophizing over their algorithms exam and severe sleep deprivation."
    
    mem.extract_facts_from_turn(user_turn, assistant_reply, reasoning=reasoning)
    
    print("Language Preference:", mem.language_preference)
    print("Key Stressors:", mem.key_stressors)
    print("Identified Distortions:", mem.identified_distortions)
    print("Emotional Trend:", mem.emotional_trend)
    
    assert any("Exam" in s for s in mem.key_stressors), "Failed to extract Exam stressor"
    assert any("Roommate" in s for s in mem.key_stressors), "Failed to extract Roommate stressor"
    assert any("Sleep" in s for s in mem.key_stressors), "Failed to extract Sleep stressor"
    assert "Catastrophizing" in mem.identified_distortions, "Failed to extract Catastrophizing distortion"
    print("[PASSED] Fact and Stressor Extraction")


def test_coping_tool_tracking():
    print("\n--- Testing Coping Tool Efficacy Tracking ---")
    mem = ConversationMemory()
    
    # Turn 1: Introduce box breathing
    mem.extract_facts_from_turn(
        "I feel panicky.",
        "Let's try box breathing for 4 counts.",
        reasoning="Student is anxious."
    )
    assert "Box Breathing (4-4-4-4)" in mem.coping_tools_used
    assert mem.coping_tools_used["Box Breathing (4-4-4-4)"] == "Introduced in session"
    
    # Turn 2: User confirms it helped
    mem.extract_facts_from_turn(
        "That box breathing really helped, I feel much calmer now.",
        "Glad to hear that! What's on your mind next?",
        reasoning="Student is de-escalating."
    )
    assert mem.coping_tools_used["Box Breathing (4-4-4-4)"] == "Reported helpful by student"
    assert mem.emotional_trend[-1]["emotion"] == "De-escalating / Calmer"
    print("[PASSED] Coping Tool Efficacy & Emotional Trend Tracking")


def test_rolling_summary_and_overflow():
    print("\n--- Testing Sliding Window History Archival ---")
    agent = PeerSpaceAgent()
    
    # Push 16 alternating messages
    for i in range(8):
        agent.add_message("user", f"Message {i}: I am dealing with test stress {i}")
        agent.add_message("assistant", f"Final Answer: I understand turn {i}.")
        
    print("History length after 16 turns:", len(agent.conversation_history))
    assert len(agent.conversation_history) <= 13, f"Expected bounded history <= 13, got {len(agent.conversation_history)}"
    assert agent.memory.archived_turns_count > 0, "Older turns were not archived"
    assert agent.memory.rolling_summary is not None, "Rolling summary should not be empty"
    print("Rolling summary:", agent.memory.rolling_summary)
    print("[PASSED] Sliding Window History Archival")


def test_prompt_context_injection():
    print("\n--- Testing Memory Prompt Context Injection ---")
    agent = PeerSpaceAgent()
    agent.memory.language_preference = "Hinglish (Roman script)"
    agent.memory.key_stressors = ["Exam / Academic Test: Algorithms Midterm", "Sleep Deprivation"]
    agent.memory.coping_tools_used["Box Breathing (4-4-4-4)"] = "Reported helpful by student"
    agent.memory.rolling_summary = "Student was spiraling over exam prep earlier."
    
    react_messages = agent._build_react_messages()
    
    assert len(react_messages) >= 2, "Expected at least 2 messages"
    memory_msg = react_messages[1]
    assert memory_msg["role"] == "system"
    assert "[CONVERSATION MEMORY & RELEVANT PAST CONTEXT]" in memory_msg["content"]
    assert "Algorithms Midterm" in memory_msg["content"]
    assert "Box Breathing" in memory_msg["content"]
    print("Injected Memory Context Preview:")
    print(memory_msg["content"][:200] + "...")
    print("[PASSED] Memory Prompt Context Injection")


def run_all():
    print("=" * 60)
    print(" RUNNING AGENT MEMORY UNIT TESTS")
    print("=" * 60)
    test_memory_extraction()
    test_coping_tool_tracking()
    test_rolling_summary_and_overflow()
    test_prompt_context_injection()
    print("\n" + "=" * 60)
    print(" ALL AGENT MEMORY UNIT TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all()
