"""
PeerSpace AI CBT & Safety Tools
Provides distortion analysis, grounding exercises, campus resources, and counselor alerts.
"""

import re
import uuid
from datetime import datetime
from collections import deque
from typing import List, Dict, Optional

# In-memory mood tracking log bounded to max 100 entries to prevent memory exhaustion
SESSION_MOOD_LOG = deque(maxlen=100)

# Structured Counselor & Professional Intervention Alert Queue (bounded to 200 entries)
COUNSELOR_ALERTS: List[Dict] = []
MAX_ALERTS = 200

# Context holder for current executing session metadata
CURRENT_SESSION_CONTEXT = {
    "session_id": "anon-session",
    "alias": "Anonymous Student"
}

def set_session_context(session_id: str, alias: str):
    """Sets session metadata for tool tracking."""
    CURRENT_SESSION_CONTEXT["session_id"] = session_id
    CURRENT_SESSION_CONTEXT["alias"] = alias

def _sanitize_tool_input(text: str, max_chars: int = 1000) -> str:
    """Sanitizes and bounds string length for tool parameters."""
    if not isinstance(text, str):
        text = str(text)
    clean = text.replace("\x00", "").strip()
    return clean[:max_chars]


def escalate_counselor_intervention(reason_and_severity: str) -> str:
    """
    Triggers an immediate Counselor Alert and schedules professional intervention
    when acute self-harm risk, severe trauma, or clinical crisis is detected.
    """
    cleaned = _sanitize_tool_input(reason_and_severity, max_chars=300)
    
    severity = "HIGH"
    if "critical" in cleaned.lower() or "suicide" in cleaned.lower() or "kill" in cleaned.lower() or "die" in cleaned.lower():
        severity = "CRITICAL"
    elif "medium" in cleaned.lower() or "moderate" in cleaned.lower():
        severity = "MEDIUM"

    alert_id = str(uuid.uuid4())[:8]
    alert_entry = {
        "id": alert_id,
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "session_id": CURRENT_SESSION_CONTEXT.get("session_id", "anon-session"),
        "alias": CURRENT_SESSION_CONTEXT.get("alias", "Anonymous Student"),
        "severity": severity,
        "reason": cleaned,
        "recommended_action": "On-call campus counselor notified. Maintain warm peer support and share 24/7 helplines (Jeevan Aastha: 1800 233 3330, Tele-MANAS: 1800 891 4416, Aasra: 09820466726, Kiran: 1800 599 0019).",
        "status": "PENDING"
    }

    # Bounded insertion
    if len(COUNSELOR_ALERTS) >= MAX_ALERTS:
        COUNSELOR_ALERTS.pop(0)
    COUNSELOR_ALERTS.append(alert_entry)

    return (
        f"PROFESSIONAL INTERVENTION ALERT #{alert_id} LOGGED [{severity}]: "
        f"Campus counseling team has been alerted. "
        f"Instructions for Peer Coach: Stay compassionate, calm, and reassuring. "
        f"Share Jeevan Aastha (1800 233 3330), Tele-MANAS (1800 891 4416 / 14416), Aasra (09820466726), or Kiran (1800 599 0019) gently without alarming the student."
    )


def get_counselor_alerts() -> List[Dict]:
    """Returns all counselor alerts sorted by newest first."""
    return list(reversed(COUNSELOR_ALERTS))


def update_counselor_alert(alert_id: str, new_status: str) -> bool:
    """Updates the status of a counselor alert ('DISPATCHED', 'RESOLVED')."""
    for alert in COUNSELOR_ALERTS:
        if alert["id"] == alert_id:
            alert["status"] = new_status
            return True
    return False


def cbt_distortion_identifier(thought: str) -> str:
    """
    Analyzes a student's negative thought to identify common Cognitive Distortions
    and provide peer-friendly CBT reframing angles and Socratic inquiry prompts.
    """
    thought = _sanitize_tool_input(thought)
    if not thought:
        return "CBT Analysis: No specific thought provided to analyze."

    t_lower = thought.lower()
    distortions_found = []
    
    # 1. Catastrophizing / Fortune Telling
    if any(k in t_lower for k in ["ruined", "never going to", "end of the world", "i'm doomed", "i'm cooked", "my life is over", "gonna fail everything", "everything is ruined", "it's over"]):
        distortions_found.append({
            "type": "Catastrophizing / Fortune Telling",
            "meaning": "Assuming the absolute worst-case scenario will definitely happen.",
            "reframing_prompt": "Acknowledge the fear, then gently ask what a realistic middle-ground outcome might look like, or what they can control right now."
        })
        
    # 2. All-or-Nothing / Black-and-White Thinking
    if any(k in t_lower for k in ["always", "never", "everyone", "nobody", "total failure", "completely useless", "all my friends", "every single time"]):
        distortions_found.append({
            "type": "All-or-Nothing / Black-and-White Thinking",
            "meaning": "Viewing things in total extremes (success vs failure) with no gray area.",
            "reframing_prompt": "Help them spot exceptions or partial wins. Ask if there's any middle ground between complete perfection and total disaster."
        })
        
    # 3. Mind Reading
    if any(k in t_lower for k in ["they think i'm", "everyone thinks", "prof hates me", "she hates me", "he thinks i'm stupid", "they are judging me", "people probably laugh"]):
        distortions_found.append({
            "type": "Mind Reading",
            "meaning": "Assuming you know what other people are thinking or judging about you.",
            "reframing_prompt": "Gently explore if there is hard evidence for that thought, or if our anxiety is making assumptions about what others think."
        })
        
    # 4. Should / Must Statements
    if any(k in t_lower for k in ["i should have", "i must", "i ought to", "i shouldn't be feeling", "i have to be doing more"]):
        distortions_found.append({
            "type": "Should / Must Statements",
            "meaning": "Placing rigid, guilt-inducing expectations on oneself.",
            "reframing_prompt": "Normalize taking breaks and being human. Encourage replacing 'I should' with 'It would be nice if, but it's okay to take things step by step.'"
        })
        
    # 5. Emotional Reasoning
    if any(k in t_lower for k in ["i feel stupid so i am", "i feel like a loser", "feels hopeless", "i feel like nobody likes me"]):
        distortions_found.append({
            "type": "Emotional Reasoning",
            "meaning": "Treating intense emotions as objective facts about self-worth.",
            "reframing_prompt": "Validate the heavy feeling, while separating emotional state from reality ('Feeling overwhelmed doesn't mean you're incapable')."
        })

    if not distortions_found:
        return (
            "CBT Analysis: Negative thought pattern detected. "
            "Suggest exploring the underlying belief: 'What is the thought telling you right now, "
            "and what would you say to a close friend in this exact situation?'"
        )

    summary_lines = ["Identified Cognitive Distortions:"]
    for d in distortions_found:
        summary_lines.append(f"- {d['type']}: {d['meaning']} | Strategy: {d['reframing_prompt']}")
    
    return "\n".join(summary_lines)


def crisis_safety_check(user_message: str) -> str:
    """
    Evaluates risk and provides campus crisis helpline information in a warm, peer-accessible tone.
    Automatically escalates a Counselor Alert if critical keywords are detected.
    """
    user_message = _sanitize_tool_input(user_message)
    msg_lower = user_message.lower()
    crisis_keywords = ["suicide", "kill myself", "want to die", "end my life", "self harm", "hurt myself", "no reason to live", "better off dead"]
    
    is_crisis = any(k in msg_lower for k in crisis_keywords)
    
    if is_crisis:
        # Trigger counselor alert behind the scenes
        escalate_counselor_intervention(f"Crisis safety alert triggered for statement: {user_message[:100]}")
        return (
            "CRISIS ALERT: The user may be experiencing acute distress or self-harm thoughts. "
            "Immediate peer action: Respond with extreme warmth, validating care, and human empathy. "
            "Remind them they are not alone and share these 24/7 free and confidential crisis helplines gently: "
            "1. Jeevan Aastha Helpline: 1800 233 3330 (24/7 Toll-Free) "
            "2. Aasra: 09820466726 / 9820466726 (24/7 Support) "
            "3. Tele-MANAS: 1800 891 4416 or dial 14416 (National 24/7 Mental Health Helpline) "
            "4. Kiran Mental Health: 1800 599 0019 (24/7 Multi-lingual Support) "
            "Stay present with them, do not judge, and encourage reaching out to a counselor or someone safe right now."
        )
    return "Crisis Safety Check: No immediate acute safety crisis keywords detected. Proceed with standard empathetic peer support."


def calming_exercise_guide(exercise_type: str) -> str:
    """
    Provides step-by-step guidance for peer-delivered calming and grounding techniques.
    """
    exercise_type = _sanitize_tool_input(exercise_type, max_chars=200)
    ext_lower = exercise_type.lower()
    
    if "4-7-8" in ext_lower or "breathing" in ext_lower or "box" in ext_lower:
        return (
            "Calming Exercise - Box Breathing / 4-7-8:\n"
            "1. Inhale slowly through your nose for 4 seconds.\n"
            "2. Hold your breath gently for 4 seconds (or 7s for 4-7-8).\n"
            "3. Exhale smoothly through your mouth for 4 seconds (or 8s).\n"
            "4. Pause for 4 seconds, then repeat 3-4 times.\n"
            "Peer tip: Offer to do a round together right in the chat."
        )
    elif "grounding" in ext_lower or "54321" in ext_lower or "5-4-3-2-1" in ext_lower or "panic" in ext_lower or "anxiety" in ext_lower:
        return (
            "Calming Exercise - 5-4-3-2-1 Sensory Grounding:\n"
            "1. Notice 5 things you can see around your room right now.\n"
            "2. 4 things you can physically feel (e.g. feet on the floor, sweater fabric).\n"
            "3. 3 things you can hear (e.g. AC hum, birds, keyboard taps).\n"
            "4. 2 things you can smell or like the smell of.\n"
            "5. 1 good thing you can taste or one positive word about yourself.\n"
            "Peer tip: Ask them to name 2 things they can see right now to get started."
        )
    elif "defusion" in ext_lower or "leaves" in ext_lower or "thoughts" in ext_lower:
        return (
            "Calming Exercise - Thought Defusion (Leaves on a Stream):\n"
            "Picture sitting by a quiet stream with leaves floating by. "
            "Whenever an anxious thought pops up, place it gently on a leaf and watch it float down the river without fighting it."
        )
    else:
        return (
            "Calming Exercise - Quick Reset:\n"
            "Take one deep breath: inhale for 4s, exhale slowly for 6s with your shoulders dropped. "
            "Remind yourself you only need to handle this exact moment."
        )


def campus_resources_lookup(category: str) -> str:
    """
    Provides anonymous campus wellness and student support resources.
    """
    category = _sanitize_tool_input(category, max_chars=200)
    cat_lower = category.lower()
    
    if "academic" in cat_lower or "exam" in cat_lower or "study" in cat_lower or "grade" in cat_lower:
        return (
            "Campus Academic Support:\n"
            "- Student Learning & Tutoring Center (Walk-in peer tutoring & study strategies)\n"
            "- Academic Advising & Course Load Deferral Support\n"
            "- Campus Writing Center (Paper feedback & thesis planning)"
        )
    elif "counseling" in cat_lower or "therapy" in cat_lower or "mental" in cat_lower:
        return (
            "Campus Mental Health & Counseling Services:\n"
            "- Student Counseling Center (Free confidential individual & group sessions)\n"
            "- 24/7 Campus Crisis & Support Line: Call campus dispatch or ext. 4357 (HELP)\n"
            "- Anonymous Peer Listening Drop-in Hours: Mon-Fri 6 PM - 11 PM"
        )
    elif "sleep" in cat_lower or "wellness" in cat_lower or "burnout" in cat_lower:
        return (
            "Campus Wellness & Mind-Body Center:\n"
            "- Campus Relaxation & Nap Pods (Student Union 3rd floor)\n"
            "- Guided Meditation & Yoga Workshops (Tues/Thurs 5 PM)\n"
            "- Nutrition & Sleep Hygiene consultations"
        )
    else:
        return (
            "General Campus Student Support:\n"
            "- Dean of Students Office (Emergency academic accommodations & hardship funds)\n"
            "- Anonymous Campus Peer Chat Hotline (PeerSpace 24/7)\n"
            "- Campus Recreation & Wellness Center"
        )


def mood_journal_tracker(mood_and_trigger: str) -> str:
    """
    Records student emotional check-in for the current session.
    """
    entry = _sanitize_tool_input(mood_and_trigger, max_chars=200)
    if entry:
        SESSION_MOOD_LOG.append(entry)
    return f"Mood logged successfully: '{entry}'. Total check-ins logged: {len(SESSION_MOOD_LOG)}."


AVAILABLE_TOOLS = {
    "cbt_distortion_identifier": cbt_distortion_identifier,
    "crisis_safety_check": crisis_safety_check,
    "calming_exercise_guide": calming_exercise_guide,
    "campus_resources_lookup": campus_resources_lookup,
    "mood_journal_tracker": mood_journal_tracker,
    "escalate_counselor_intervention": escalate_counselor_intervention,
}
