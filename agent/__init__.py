"""
PeerSpace AI Agent Package
Empathetic CBT Peer Mental Health Coach
"""

from agent.agent import PeerSpaceAgent
from agent.tools import (
    AVAILABLE_TOOLS,
    set_session_context,
    get_counselor_alerts,
    update_counselor_alert,
    COUNSELOR_ALERTS
)

__all__ = [
    "PeerSpaceAgent",
    "AVAILABLE_TOOLS",
    "set_session_context",
    "get_counselor_alerts",
    "update_counselor_alert",
    "COUNSELOR_ALERTS"
]
