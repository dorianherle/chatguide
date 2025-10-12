"""Routes container - tracks which routes fired."""

from typing import List, Dict, Set


class Routes:
    """Tracks route execution state.
    
    All attributes are directly editable:
        routes.fired_this_turn.append("route_0")
        routes.last_fired["route_0"] = 5
    """
    
    def __init__(self):
        self.fired_this_turn: List[str] = []           # Routes that fired this turn
        self.fired_history: List[List[str]] = []       # Routes fired each turn (historical)
        self.last_fired: Dict[str, int] = {}           # route_id -> turn_number
        self.executed_once: Set[str] = set()           # Routes that have fired at least once
    
    def clear_turn(self):
        """Clear this turn's fired routes (call at start of each turn)."""
        self.fired_this_turn = []
    
    def mark_fired(self, route_id: str, turn_count: int):
        """Mark a route as fired."""
        self.fired_this_turn.append(route_id)
        self.last_fired[route_id] = turn_count
        self.executed_once.add(route_id)
    
    def save_turn_history(self):
        """Save current turn's fired routes to history."""
        self.fired_history.append(self.fired_this_turn.copy())
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "fired_this_turn": self.fired_this_turn.copy(),
            "fired_history": [turn.copy() for turn in self.fired_history],
            "last_fired": self.last_fired.copy(),
            "executed_once": list(self.executed_once)
        }

