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
from agent.tools import AVAILABLE_TOOLS, set_session_context
from agent.prompts import SYSTEM_PROMPT
from agent.memory import ConversationMemory

# Load environment configuration
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment or .env file.")

client = Groq(api_key=api_key)

MAX_CONTEXT_MESSAGES = 12
MAX_INPUT_LENGTH = 2000
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


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

    def chat(self, user_message: str, session_id: str = "anon-session", alias: str = "Anonymous Student", max_steps: int = 5) -> str:
        """
        Executes the ReAct loop dynamically with session tracking and intervention triggers.
        """
        import time
        user_message = self._sanitize_input(user_message)
        if not user_message:
            return ""

        # Set session context for tool tracing (e.g. counselor alerts)
        set_session_context(session_id, alias)

        # Automatic safety guardrail: evaluate safety and trigger counselor alert if critical risk is detected
        try:
            self.tools["crisis_safety_check"](user_message)
        except Exception:
            pass

        # Append student message to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self._trim_history()

        step_messages = self._build_react_messages()
        final_response = ""

        for step in range(max_steps):
            if self.verbose:
                print(f"\n[ReAct Step {step + 1}]")

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

            # Check if Final Answer is generated
            final_ans = self._extract_final_answer(output)
            if final_ans is not None:
                final_response = final_ans
                break

            # Check if an Action is requested
            tool_name, tool_input = self._extract_action(output)
            if tool_name:
                if self.verbose:
                    print(f"\n[Action]: {tool_name}(\"{tool_input}\")")

                if tool_name in self.tools:
                    try:
                        observation = self.tools[tool_name](tool_input)
                    except Exception:
                        observation = "Error executing tool safely."
                else:
                    observation = f"Tool '{tool_name}' not recognized."

                if self.verbose:
                    print(f"\n[Observation]:\n{observation}")

                step_messages.append({"role": "assistant", "content": output})
                step_messages.append({"role": "user", "content": f"Observation: {observation}"})
            else:
                final_response = self._clean_student_response(output)
                break

        # Single-purpose guardrail: If code or algorithms were somehow produced, pivot in user's language
        if self._contains_disallowed_code(final_response):
            lang = self._detect_user_language(user_message)
            if lang == "hinglish":
                final_response = "Yaar coding ya homework toh mere bas ki nahi hai, par lagta hai assignment ka bohot load hai. Kaisa feel ho raha hai?"
            elif lang == "hindi":
                final_response = "मैं कोडिंग या होमवर्क तो नहीं कर सकता, पर ऐसा लग रहा है कि पढ़ाई का काफ़ी तनाव है। कैसा महसूस कर रहे हो?"
            else:
                final_response = "I'm really not the person for coding or technical work, but it sounds like you've got a lot of assignment pressure right now. How is your workload feeling?"

        # Ensure internal reasoning or thoughts never leak into user-facing reply
        final_response = self._clean_student_response(final_response)

        if not final_response:
            final_response = self._get_fallback_message(user_message, connection_drop=False)

        # Ensure no accidental counselor prefix persists in final response
        final_response = re.sub(r'^(?:\[COUNSELOR\]:?|Counselor:?)\s*', '', final_response, flags=re.IGNORECASE).strip()

        self.conversation_history.append({"role": "assistant", "content": f"Final Answer: {final_response}"})

        # Update memory with turn facts, emotional trajectory, and CBT state
        if hasattr(self, "memory") and self.memory:
            try:
                self.memory.extract_facts_from_turn(user_message, final_response, reasoning=self.last_reasoning)
            except Exception:
                pass

        return final_response
