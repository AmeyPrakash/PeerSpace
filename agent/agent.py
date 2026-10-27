"""
PeerSpace ReAct CBT Agent
Maintains conversation memory, executes tool actions, and provides short empathetic peer responses.
"""

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Tuple
from groq import Groq
from agent.tools import (
    AVAILABLE_TOOLS,
    TOOL_REGISTRY,
    set_session_context,
    execute_tool_securely,
    escalate_counselor_intervention
)
from agent.prompts import SYSTEM_PROMPT
from agent.memory import ConversationMemory

# Load environment configuration
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=api_key or "gsk_placeholder_key_for_build")

MAX_CONTEXT_MESSAGES = 12
MAX_INPUT_LENGTH = 2000
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_ITERATIONS = 4
MAX_TOOL_BUDGET = 3


class PeerSpaceAgent:
    def __init__(self, model_name: str = DEFAULT_MODEL, verbose: bool = False):
        self.model_name = model_name
        self.verbose = verbose
        self.tools = AVAILABLE_TOOLS
        self.memory = ConversationMemory()
        self.conversation_history = []
        self.last_reasoning: Optional[str] = None
        self.reasoning_history: List[Dict[str, Any]] = []
        self.reset_session()

    def reset_session(self):
        """Clears conversation memory and resets with system prompt."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.last_reasoning = None
        self.reasoning_history = []
        if hasattr(self, "memory") and self.memory:
            self.memory.clear()

    def add_message(self, role: str, content: str):
        """Appends a message to conversation history with automatic history trimming."""
        self.conversation_history.append({"role": role, "content": content})
        self._trim_history()

    def _sanitize_input(self, text: str) -> str:
        """Sanitizes user input by stripping null bytes, controlling characters, and capping length."""
        if not isinstance(text, str):
            text = str(text)
        clean = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return clean.strip()[:MAX_INPUT_LENGTH]

    def _trim_history(self):
        """Maintains bounded memory while archiving older messages into rolling memory."""
        if len(self.conversation_history) > MAX_CONTEXT_MESSAGES + 1:
            system_msg = self.conversation_history[0]
            dropped_msgs = self.conversation_history[1 : len(self.conversation_history) - MAX_CONTEXT_MESSAGES]
            if hasattr(self, "memory") and self.memory and dropped_msgs:
                self.memory.archive_and_condense(dropped_msgs)
            recent_msgs = self.conversation_history[-MAX_CONTEXT_MESSAGES:]
            self.conversation_history = [system_msg] + recent_msgs

    def _extract_action(self, text: str):
        """Extracts tool name and arguments securely."""
        match = re.search(r"Action:\s*([a-zA-Z0-9_]{1,50})\(\s*[\"']?(.*?)[\"']?\s*\)", text, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            tool_input = match.group(2).strip().strip('"\'')[:500]
            return tool_name, tool_input
        return None, None

    def _contains_disallowed_code(self, text: str) -> bool:
        """Detects if the response accidentally generated code or algorithms instead of peer coaching."""
        code_patterns = [
            r"```[a-zA-Z]*",
            r"def\s+[a-zA-Z_][a-zA-Z0-9_]*\(",
            r"class\s+[a-zA-Z_][a-zA-Z0-9_]*[\(:]",
            r"import\s+[a-zA-Z_]",
            r"#include\s+<",
            r"public\s+static\s+void\s+main",
            r"function\s+[a-zA-Z_][a-zA-Z0-9_]*\("
        ]
        return any(re.search(p, text) for p in code_patterns)

    def _detect_user_language(self, text: str) -> str:
        """Detects whether text is Hindi (Devanagari), Hinglish (Roman script), or English/Other."""
        if re.search(r'[\u0900-\u097F]', text):
            return "hindi"
        
        hinglish_words = {
            "bhai", "yaar", "bohot", "bahut", "zyada", "jyada", "kya", "karu", "karoon", 
            "kaise", "samajh", "nahi", "nhi", "aa", "raha", "rahi", "hai", "hain", "ho", 
            "hoga", "tension", "load", "mat", "le", "bata", "mujhe", "mera", "meri", 
            "tere", "teri", "sab", "kuch", "shuru", "lagta", "lag", "accha", "theek",
            "par", "aur", "ab", "karna", "baat", "saath", "dost"
        }
        words = set(re.findall(r'[a-zA-Z]+', text.lower()))
        if len(words.intersection(hinglish_words)) >= 2 or any(w in words for w in ["bhai", "yaar", "bohot", "samajh", "karu"]):
            return "hinglish"
            
        return "other"

    def _get_fallback_message(self, user_message: str, connection_drop: bool = False) -> str:
        """Returns friendly fallback response matching the user's language and tone (1-3 sentences)."""
        lang = self._detect_user_language(user_message)
        if connection_drop:
            if lang == "hindi":
                return "माफ़ करना, मेरा कनेक्शन एक पल के लिए कट गया था। क्या तुम अपनी बात फिर से बता सकते हो?"
            elif lang == "hinglish":
                return "Yaar connection thoda drop ho gaya tha. Ek baar phir se batana kya baat chal rahi thi?"
            else:
                return "My connection dipped for a moment there. Could you say that one more time?"
        else:
            if lang == "hindi":
                return "मैं यहीं हूँ। जो भी बात है, आराम से बताओ—कोई जल्दबाज़ी नहीं है।"
            elif lang == "hinglish":
                return "Bhai main yahin hoon. Tension mat le, aaram se bata kya baat hai."
            else:
                return "Take your time—it's okay. What's on your mind right now?"

    def _extract_reasoning(self, text: str) -> Optional[str]:
        """
        Extracts internal reasoning/thoughts that analyze information and decide what to do.
        Matches 'Reasoning: ...' up to 'Action:', 'Final Answer:', or end of string.
        """
        match = re.search(r"(?:Reasoning|Thought):\s*(.*?)(?=\n(?:Action|Final Answer|Observation):|\Z)", text, re.DOTALL | re.IGNORECASE)
        if match:
            reasoning = match.group(1).strip()
            return reasoning if reasoning else None
        return None

    def _extract_final_answer(self, text: str) -> Optional[str]:
        """Extracts the final user-facing answer string, ensuring no internal reasoning leaks."""
        if "Final Answer:" in text:
            parts = text.split("Final Answer:", 1)
            ans = parts[1].strip()
            # Strip any trailing reasoning or action directives
            ans = re.split(r'\n(?:Reasoning|Thought|Action):', ans, flags=re.IGNORECASE)[0].strip()
            return ans
        return None

    def _clean_student_response(self, text: str) -> str:
        """Strips out internal Reasoning:, Thought:, and Action: directives to prevent leakages."""
        clean = text
        if "Final Answer:" in clean:
            clean = clean.split("Final Answer:", 1)[1]
        # Strip leading Reasoning block if present
        clean = re.sub(r'^(?:Reasoning|Thought):\s*.*?(?=(?:\n\n|\n[A-Z]|\Z))', '', clean, flags=re.DOTALL | re.IGNORECASE)
        # Strip any Action syntax
        clean = re.sub(r'Action:\s*[a-zA-Z0-9_]+\(.*?\)', '', clean, flags=re.DOTALL | re.IGNORECASE)
        return clean.strip()

    def _build_react_messages(self) -> List[Dict[str, str]]:
        """
        Harmonizes conversation history for the LLM ReAct loop.
        Converts counselor interventions into clean system context notes so the AI
        maintains its peer persona and ReAct 'Final Answer:' syntax without format clashing.
        """
        messages = []
        counselor_notes = []

        for msg in self.conversation_history:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "system":
                messages.append(msg)
                continue

            # Detect counselor intervention messages
            if "[COUNSELOR" in content:
                clean_text = re.sub(r'\[COUNSELOR.*?\]:?', '', content).strip()
                if clean_text:
                    counselor_notes.append(clean_text)
                continue

            # If counselor notes were accumulated, inject them as a system context note
            if counselor_notes:
                summary = " | ".join(counselor_notes)
                messages.append({
                    "role": "system",
                    "content": (
                        f"[Context Note: A university counselor stepped in to support the student earlier: \"{summary}\". "
                        "The counselor has now left. You are back as the warm student peer CBT coach. "
                        "Do NOT adopt a counselor persona; remain a supportive student classmate.]"
                    )
                })
                counselor_notes.clear()

            # Ensure assistant messages in history have proper Final Answer: formatting
            if role == "assistant" and not content.startswith("Final Answer:"):
                messages.append({"role": "assistant", "content": f"Final Answer: {content}"})
            else:
                messages.append(msg)

        if counselor_notes:
            summary = " | ".join(counselor_notes)
            messages.append({
                "role": "system",
                "content": (
                    f"[Context Note: A university counselor stepped in to support the student earlier: \"{summary}\". "
                    "The counselor has now left. You are back as the warm student peer CBT coach.]"
                )
            })

        # Inject memory context if available
        if hasattr(self, "memory") and self.memory and self.memory.has_context():
            mem_context = self.memory.get_memory_prompt_context()
            if mem_context:
                messages.insert(1, {"role": "system", "content": mem_context})

        return messages

    def _extract_actions(self, text: str) -> List[Tuple[str, str]]:
        """Extracts all tool actions (name and input argument) from text."""
        matches = re.findall(r"Action:\s*([a-zA-Z0-9_]{1,50})\(\s*[\"']?(.*?)[\"']?\s*\)", text, re.DOTALL)
        actions = []
        for name, arg in matches:
            actions.append((name.strip(), arg.strip().strip('"\'')[:500]))
        return actions

    def _pre_generation_safety_check(self, user_message: str, session_id: str, alias: str) -> Optional[str]:
        """
        Pre-generation safety check. If acute crisis or self-harm risk is detected,
        immediately alerts on-duty campus counselors and activates an instant, prioritized
        crisis response path with 24/7 helplines in the student's language.
        """
        msg_lower = user_message.lower()
        crisis_keywords = [
            "suicide", "kill myself", "want to die", "end my life", "self harm",
            "hurt myself", "no reason to live", "better off dead", "marne ka man",
            "khatam kar lunga", "jeene ka man nahi", "khud ko nuksan", "end it all"
        ]
        if any(k in msg_lower for k in crisis_keywords):
            # Dispatch emergency counselor alert
            try:
                escalate_counselor_intervention(f"Crisis safety alert for statement: {user_message[:120]}")
            except Exception:
                pass

            lang = self._detect_user_language(user_message)
            if lang == "hindi":
                return (
                    "मैं तुम्हारी बात सुन रहा हूँ, और तुम अकेले नहीं हो—तुम्हारी ज़िंदगी बहुत कीमती है। "
                    "कृपया तुरंत Tele-MANAS (14416 / 1800 891 4416), जीवन आस्था (1800 233 3330), या आसरा (09820466726) पर कॉल करें। "
                    "हमने कैंपस सपोर्ट टीम को भी सूचित कर दिया है। मैं यहीं हूँ—आराम से बताओ अभी क्या चल रहा है?"
                )
            elif lang == "hinglish":
                return (
                    "Bhai main tumhari baat sun raha hoon, aur tum bilkul akele nahi ho—tumhari zindagi bohot keemti hai. "
                    "Please turant kisi safe insaan ya helpline se connect karo: Tele-MANAS (14416 / 1800 891 4416), Jeevan Aastha (1800 233 3330), ya Aasra (09820466726). "
                    "Humne campus counselor team ko bhi alert bhej diya hai. Main yahin hoon tumhare saath, kya ho raha hai?"
                )
            else:
                return (
                    "I hear you, and please know that you are not alone and your life matters deeply. "
                    "Please reach out right now to free 24/7 professional support: Tele-MANAS (14416 / 1800 891 4416), Jeevan Aastha (1800 233 3330), or Aasra (09820466726). "
                    "Our on-call campus counseling team has also been alerted. I'm right here with you—what's happening right now?"
                )
        return None

    def _post_generation_safety_check(self, text: str, user_message: str, executed_tools: List[str]) -> str:
        """
        Post-generation safety and quality check:
        1. Strips internal reasoning, thought, and action tags.
        2. Detects and corrects fabricated external action confirmations.
        3. Prevents code/homework generation and redirects warmly.
        4. Strips leaked directives or roleplay prefixes.
        """
        clean = self._clean_student_response(text)

        # 2. Prevent fabricated action confirmations when no tool backed it
        fabricated_checks = [
            (r"\b(?:i (?:have )?(?:booked|scheduled|confirmed|reserved)\b.*?\b(?:appointment|session|slot))\b",
             "I can't directly book appointments for you, but you can schedule a 1-on-1 session right through the Counselor Portal."),
            (r"\b(?:i (?:have )?(?:called|emailed|contacted|notified|spoken to)\b.*?\b(?:professor|dean|advisor|police|dispatch))\b",
             "As a peer coach, I can't contact university staff on your behalf, but you can reach out directly to the Dean of Students or Counseling Center."),
            (r"\b(?:i (?:have )?(?:dropped|withdrawn|cancelled)\b.*?\b(?:course|class|exam|test))\b",
             "I don't have access to your academic records to drop courses, but your academic advisor can help you review your options.")
        ]
        for pattern, correction in fabricated_checks:
            if re.search(pattern, clean, re.IGNORECASE):
                clean = re.sub(pattern, correction, clean, flags=re.IGNORECASE)

        # 3. Disallowed code / trivia deflection
        if self._contains_disallowed_code(clean):
            lang = self._detect_user_language(user_message)
            if lang == "hinglish":
                clean = "Yaar coding ya homework toh mere bas ki nahi hai, par lagta hai assignment ka bohot load hai. Kaisa feel ho raha hai?"
            elif lang == "hindi":
                clean = "मैं कोडिंग या होमवर्क तो नहीं कर सकता, पर ऐसा लग रहा है कि पढ़ाई का काफ़ी तनाव है। कैसा महसूस कर रहे हो?"
            else:
                clean = "I'm really not the person for coding or technical work, but it sounds like you've got a lot of assignment pressure right now. How is your workload feeling?"

        # 4. Clean leading/trailing artifacts
        clean = re.sub(r'^(?:\[COUNSELOR\]:?|Counselor:?)\s*', '', clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r'^(?:Observation|Action|Final Answer):\s*', '', clean, flags=re.IGNORECASE).strip()
        return clean

    def chat(
        self,
        user_message: str,
        session_id: str = "anon-session",
        alias: str = "Anonymous Student",
        user_role: str = "student",
        max_steps: int = MAX_ITERATIONS,
        tool_budget: int = MAX_TOOL_BUDGET
    ) -> str:
        """
        Executes the complete AI agent orchestration loop:
        1. Pre-generation safety check with separate crisis fast-path.
        2. Ephemeral in-RAM memory context injection.
        3. Multi-turn ReAct reasoning and tool-calling with strict iteration & budget limits.
        4. Validated and authorized tool execution.
        5. Direct conversational responses without unnecessary tool calls.
        6. Post-generation safety validation and anti-fabrication enforcement.
        """
        import time
        user_message = self._sanitize_input(user_message)
        if not user_message:
            return ""

        # Bind session context for tool tracking (e.g. counselor alerts)
        set_session_context(session_id, alias)

        # 1. Pre-generation Safety Check & Crisis Fast-Path
        crisis_reply = self._pre_generation_safety_check(user_message, session_id, alias)
        if crisis_reply:
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": f"Final Answer: {crisis_reply}"})
            self._trim_history()
            if hasattr(self, "memory") and self.memory:
                try:
                    self.memory.extract_facts_from_turn(user_message, crisis_reply, reasoning="Acute crisis risk detected; activated priority crisis response path.")
                except Exception:
                    pass
            self.last_reasoning = "Acute crisis risk detected; activated priority crisis response path."
            return crisis_reply

        # 2. Append student message to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self._trim_history()

        step_messages = self._build_react_messages()
        final_response = ""
        tool_calls_executed = 0
        executed_tools_in_turn = []

        # 3. ReAct Tool-Calling Loop with iteration limit
        for step in range(max_steps):
            if self.verbose:
                print(f"\n[ReAct Step {step + 1}/{max_steps}] (Tool Budget Remaining: {tool_budget - tool_calls_executed})")

            output = ""
            for attempt in range(3):
                try:
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=step_messages,
                        temperature=0.6,
                        max_tokens=500
                    )
                    raw_content = response.choices[0].message.content or ""
                    output = raw_content.strip()
                    if output:
                        break
                    else:
                        time.sleep(0.5)
                except Exception as e:
                    if attempt < 2:
                        time.sleep(1.0)
                    else:
                        output = f"Final Answer: {self._get_fallback_message(user_message, connection_drop=True)}"

            if self.verbose:
                print(output)

            # Extract and store Reasoning step
            reasoning = self._extract_reasoning(output)
            if reasoning:
                self.last_reasoning = reasoning
                self.reasoning_history.append({
                    "step": step + 1,
                    "reasoning": reasoning
                })
                if self.verbose:
                    print(f"\n[Reasoning]:\n{reasoning}")

            # Check if Final Answer is generated directly (Conversational turn without tools)
            final_ans = self._extract_final_answer(output)
            if final_ans is not None:
                final_response = final_ans
                break

            # Check if Action(s) are requested
            actions = self._extract_actions(output)
            if actions:
                for tool_name, tool_input in actions:
                    if tool_calls_executed >= tool_budget:
                        budget_obs = f"[Tool call budget reached (max {tool_budget}). Do not invoke further tools. Synthesize your final empathetic peer response now.]"
                        step_messages.append({"role": "assistant", "content": output})
                        step_messages.append({"role": "user", "content": f"Observation: {budget_obs}"})
                        if self.verbose:
                            print(f"\n[Observation (Budget Reached)]: {budget_obs}")
                        break

                    if self.verbose:
                        print(f"\n[Action]: {tool_name}(\"{tool_input}\")")

                    # Execute tool securely with authorization and timeout enforcement
                    success, observation = execute_tool_securely(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        user_role=user_role,
                        timeout_seconds=4.0
                    )
                    tool_calls_executed += 1
                    executed_tools_in_turn.append(tool_name)

                    if self.verbose:
                        print(f"\n[Observation (Success={success})]:\n{observation}")

                    step_messages.append({"role": "assistant", "content": f"Action: {tool_name}(\"{tool_input}\")"})
                    step_messages.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                final_response = self._clean_student_response(output)
                break

        # 4. Post-generation Safety Check & Anti-Fabrication Enforcement
        final_response = self._post_generation_safety_check(final_response, user_message, executed_tools_in_turn)

        if not final_response:
            final_response = self._get_fallback_message(user_message, connection_drop=False)

        self.conversation_history.append({"role": "assistant", "content": f"Final Answer: {final_response}"})

        # 5. Update In-RAM Ephemeral Memory with turn facts and emotional trajectory
        if hasattr(self, "memory") and self.memory:
            try:
                self.memory.extract_facts_from_turn(user_message, final_response, reasoning=self.last_reasoning)
            except Exception:
                pass

        return final_response
