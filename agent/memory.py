"""
PeerSpace AI Coach Ephemeral Memory System
Stores conversation context, student stressors, emotional trajectory, and CBT state.
Zero-footprint: Operates strictly in RAM during session lifetime.
"""

import re
from typing import List, Dict, Any, Optional, Set


class ConversationMemory:
    """
    Manages structured episodic and semantic memory for an anonymous student session.
    Retains key stressors, preferred language, coping tools tried, cognitive distortions,
    and rolling context summaries across turns.
    """

    def __init__(self):
        self.language_preference: str = "english"
        self.academic_context: Optional[str] = None
        self.key_stressors: List[str] = []
        self.identified_distortions: List[str] = []
        self.coping_tools_used: Dict[str, str] = {}  # tool_name -> user feedback/status
        self.emotional_trend: List[Dict[str, Any]] = []
        self.recent_facts: List[str] = []
        self.rolling_summary: Optional[str] = None
        self.archived_turns_count: int = 0

    def clear(self):
        """Clears all session memory for reset or logout."""
        self.language_preference = "english"
        self.academic_context = None
        self.key_stressors = []
        self.identified_distortions = []
        self.coping_tools_used = {}
        self.emotional_trend = []
        self.recent_facts = []
        self.rolling_summary = None
        self.archived_turns_count = 0

    def has_context(self) -> bool:
        """Returns True if any meaningful context or facts have been remembered."""
        return bool(
            self.key_stressors
            or self.coping_tools_used
            or self.identified_distortions
            or self.rolling_summary
            or self.academic_context
            or self.recent_facts
        )

    def extract_facts_from_turn(self, user_msg: str, assistant_reply: str, reasoning: Optional[str] = None):
        """
        Extracts key stressors, academic triggers, language preferences,
        distortions, and coping mechanisms from the turn.
        """
        msg_lower = user_msg.lower()

        # 1. Detect language / dialect preference
        if re.search(r'[\u0900-\u097F]', user_msg):
            self.language_preference = "Hindi (Devanagari)"
        elif any(w in msg_lower.split() for w in ["bhai", "yaar", "bohot", "tension", "samajh", "kya", "karu", "nhi", "nahi"]):
            self.language_preference = "Hinglish (Roman script)"
        elif any(w in msg_lower.split() for w in ["fr", "cooked", "ngl", "tbh", "lowkey", "mid", "bro"]):
            self.language_preference = "English (Campus Slang)"
        else:
            self.language_preference = "English"

        # 2. Extract academic context and specific stressors
        academic_patterns = [
            (r"\b(?:midterm|midterms|finals?|exam|exams?|quiz|test)\b\s*(?:in|for|of)?\s*([a-zA-Z0-9_\s]{2,30})?", "Exam / Academic Test"),
            (r"\b(?:assignment|project|submission|lab|viva|deadline)\b\s*(?:for|in)?\s*([a-zA-Z0-9_\s]{2,30})?", "Assignment / Project Deadline"),
            (r"\b(?:gpa|cgpa|grades?|marks?|pointer|failing|failed)\b", "Academic Performance & Grades"),
            (r"\b(?:placement|placements|interview|interviews|internship|job|resume)\b", "Career / Placement Stress"),
            (r"\b(?:roommate|roommates|hostel|mess|dorm|flatmate)\b", "Hostel / Roommate Living"),
            (r"\b(?:parents?|mom|dad|family|relatives?|expectations?)\b", "Family Expectations"),
            (r"\b(?:lonely|loneliness|no friends|isolated|homesick)\b", "Social Isolation / Loneliness"),
            (r"\b(?:sleep|insomnia|tired|exhausted|burnout|haven't slept)\b", "Sleep Deprivation & Exhaustion"),
            (r"\b(?:presentation|speaking|seminar|social anxiety)\b", "Presentation / Social Anxiety"),
            (r"\b(?:breakup|relationship|\bex\b|partner|dating)\b", "Relationship Challenge")
        ]

        for pattern, stressor_label in academic_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                # Capture subject if available
                detail = match.group(0).strip()
                if detail and len(detail) < 50:
                    candidate = f"{stressor_label}: {detail.capitalize()}"
                else:
                    candidate = stressor_label
                if candidate not in self.key_stressors:
                    self.key_stressors.append(candidate)
                    if len(self.key_stressors) > 6:
                        self.key_stressors.pop(0)

        # 3. Detect emotional state & record trend
        current_emotion = self._detect_emotion(user_msg)
        if current_emotion:
            turn_idx = len(self.emotional_trend) + 1
            # Avoid consecutive duplicate records
            if not self.emotional_trend or self.emotional_trend[-1]["emotion"] != current_emotion:
                self.emotional_trend.append({
                    "turn": turn_idx,
                    "emotion": current_emotion,
                    "text_snippet": (user_msg[:60] + "...") if len(user_msg) > 60 else user_msg
                })
                if len(self.emotional_trend) > 8:
                    self.emotional_trend.pop(0)

        # 4. Extract coping tools referenced or practiced
        tool_keywords = {
            "box breathing": "Box Breathing (4-4-4-4)",
            "4-7-8": "4-7-8 Relaxing Breath",
            "5-4-3-2-1": "5-4-3-2-1 Sensory Grounding",
            "grounding": "Sensory Grounding Exercise",
            "breathing": "Deep Breathing Technique",
            "journal": "Mood Journal Reflection",
            "walk": "Outdoor Mindful Walking",
            "water": "Hydration / Grounding Pause"
        }

        full_turn_text = f"{user_msg} {assistant_reply}".lower()
        for kw, tool_name in tool_keywords.items():
            if kw in full_turn_text:
                if any(pos in msg_lower for pos in ["better", "helped", "calmer", "thanks", "working", "relaxed", "thoda accha"]):
                    self.coping_tools_used[tool_name] = "Reported helpful by student"
                elif tool_name not in self.coping_tools_used:
                    self.coping_tools_used[tool_name] = "Introduced in session"

        # 5. Extract cognitive distortions (from reasoning or assistant CBT analysis)
        if reasoning:
            distortion_matches = re.findall(
                r"(catastrophizing|all-or-nothing|black-and-white|mind reading|fortune telling|overgeneralization|emotional reasoning|should statements?)",
                reasoning,
                re.IGNORECASE
            )
            for dist in distortion_matches:
                clean_dist = dist.title()
                if clean_dist not in self.identified_distortions:
                    self.identified_distortions.append(clean_dist)

    def _detect_emotion(self, text: str) -> Optional[str]:
        """Classifies primary emotion for psychological trajectory tracking."""
        t = text.lower()
        if any(w in t for w in ["panic", "can't breathe", "shaking", "heart racing", "chest tight", "darr"]):
            return "Acute Panic / Physical Anxiety"
        if any(w in t for w in ["overwhelmed", "too much", "burnout", "exhausted", "drowning", "bohot zyada"]):
            return "Severe Overwhelm / Burnout"
        if any(w in t for w in ["stressed", "anxious", "nervous", "tension", "worried", "scared", "load"]):
            return "High Stress & Anxiety"
        if any(w in t for w in ["calmer", "better", "helping", "relaxed", "theek", "peaceful", "relief"]):
            return "De-escalating / Calmer"
        if any(w in t for w in ["sad", "crying", "depressed", "hopeless", "pointless", "alone", "lonely"]):
            return "Sadness / Dejection"
        if any(w in t for w in ["angry", "frustrated", "annoyed", "pissed", "gussa"]):
            return "Frustration / Anger"
        return None

    def archive_and_condense(self, dropped_messages: List[Dict[str, str]]):
        """
        Progressively summarizes older dropped turns so context is never lost
        when the sliding history window trims older messages.
        """
        if not dropped_messages:
            return

        user_snippets = []
        topics = []
        for m in dropped_messages:
            content = m.get("content", "")
            if m.get("role") == "user":
                user_snippets.append(content[:100])
                if any(w in content.lower() for w in ["exam", "test", "assignment", "grade", "roommate", "sleep"]):
                    topics.append(content[:60])

        self.archived_turns_count += max(1, len(dropped_messages) // 2)

        summary_parts = []
        if self.rolling_summary:
            summary_parts.append(self.rolling_summary)

        if user_snippets:
            joined = "; ".join(user_snippets[-3:])
            summary_parts.append(f"Student previously shared: \"{joined}\".")

        if self.key_stressors:
            summary_parts.append(f"Ongoing triggers: {', '.join(self.key_stressors[:3])}.")

        # Keep rolling summary concise (capped at ~350 chars)
        condensed = " ".join(summary_parts)
        if len(condensed) > 400:
            condensed = condensed[-400:]
        self.rolling_summary = condensed.strip()

    def get_memory_prompt_context(self) -> str:
        """
        Formats structured memory into a clean, token-efficient system context block
        for the ReAct prompt. Ensures the agent naturally recalls past details.
        """
        if not self.has_context():
            return ""

        lines = ["[CONVERSATION MEMORY & RELEVANT PAST CONTEXT]"]
        lines.append(f"- Student Preferred Style: {self.language_preference}")

        if self.key_stressors:
            lines.append(f"- Identified Past Stressors/Triggers: {', '.join(self.key_stressors)}")

        if self.identified_distortions:
            lines.append(f"- Tracked Cognitive Distortions: {', '.join(self.identified_distortions)}")

        if self.coping_tools_used:
            tools_str = ", ".join([f"{k} ({v})" for k, v in self.coping_tools_used.items()])
            lines.append(f"- Grounding Tools Explored: {tools_str}")

        if self.emotional_trend:
            trend_str = " -> ".join([e["emotion"] for e in self.emotional_trend[-3:]])
            lines.append(f"- Emotional Progression: {trend_str}")

        if self.rolling_summary:
            lines.append(f"- Prior Conversation Narrative: {self.rolling_summary}")

        lines.append("[Instructions: Use this past context naturally in your Reasoning and empathetic peer reply. Never recite this memory block mechanically or say 'my memory stores'. Speak like a supportive peer who remembers what they shared earlier.]")

        return "\n".join(lines)

    def get_summary_dict(self) -> Dict[str, Any]:
        """Provides structured memory telemetry for counselor dashboard."""
        return {
            "language_preference": self.language_preference,
            "key_stressors": self.key_stressors,
            "identified_distortions": self.identified_distortions,
            "coping_tools_used": self.coping_tools_used,
            "emotional_trend": self.emotional_trend,
            "rolling_summary": self.rolling_summary,
            "archived_turns_count": self.archived_turns_count
        }
