"""ClearWay AI — Shared app state (in-memory, replaces Firebase when not configured)"""
from typing import Optional, Dict, Any


class AppState:
    """Simple in-memory state store for demo mode."""
    def __init__(self):
        self.latest_optimization: Optional[Dict[str, Any]] = None
        self.data_mode: str = "DEMO"


app_state = AppState()
