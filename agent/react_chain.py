"""
Standalone ReAct Chain Runner for PeerSpace CBT Peer Coach
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from agent.tools import AVAILABLE_TOOLS
from agent.prompts import SYSTEM_PROMPT

# Load environment configuration
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

my_api_key = os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("GROQ_API_KEY not found in environment or .env")

client = Groq(api_key=my_api_key)
tools = AVAILABLE_TOOLS
system_prompt = SYSTEM_PROMPT


def _sanitize_text(text: str, max_len: int = 2000) -> str:
    """Sanitizes text by removing non-printable control characters and capping length."""
    if not isinstance(text, str):
        text = str(text)
    clean = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    return clean.strip()[:max_len]


def run_agent(student_message: str, messages_history: list = None, verbose: bool = False):
    """
    Executes the ReAct loop dynamically for a message sent from the frontend or API.
    """
    student_message = _sanitize_text(student_message)
    if not student_message:
        return ""

    if messages_history is None:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": student_message}
        ]
    else:
        messages = list(messages_history)
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": student_message})
        # Bounded sliding window
        if len(messages) > 13:
            messages = [messages[0]] + messages[-12:]

    final_response = ""

    for step in range(5):
        if verbose:
            print(f"\n[ReAct Step {step + 1}]")

        try:
            response = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
                messages=messages,
                temperature=0.6,
                max_tokens=300
            )
            raw_content = response.choices[0].message.content or ""
            answer = raw_content.strip()
        except Exception:
            answer = "Final Answer: Hey, my connection dropped for a sec. What was that again?"
        
        if verbose:
            print(answer)

        if "Final Answer:" in answer:
            final_response = answer.split("Final Answer:", 1)[1].strip()
            break

        match = re.search(r"Action:\s*([a-zA-Z0-9_]{1,50})\(\s*[\"']?(.*?)[\"']?\s*\)", answer, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            tool_input = match.group(2).strip().strip('"\'')[:500]

            if tool_name in tools:
                try:
                    observation = tools[tool_name](tool_input)
                except Exception:
                    observation = "Error executing tool."
            else:
                observation = f"Tool '{tool_name}' not found"

            if verbose:
                print(f"\nObservation: {observation}")

            messages.append({"role": "assistant", "content": answer})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
        else:
            final_response = answer
            break

    if not final_response:
        final_response = "Hey, I'm right here with you. How are things feeling right now?"

    return final_response
