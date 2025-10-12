"""Task tracking container - status, attempts, and results."""

from collections import defaultdict
from typing import Dict


class TaskTracker:
    """Tracks task status, attempts, and results.
    
    All attributes are directly editable:
        tracker.status["task1"] = "completed"
        tracker.results["name"] = "Alice"
        tracker.attempts["task1"] = 5
    """
    
    def __init__(self):
        self.status: Dict[str, str] = {}  # pending/completed/failed/active
        self.attempts: Dict[str, int] = defaultdict(int)
        self.results: Dict[str, str] = {}
    
    # Convenience method (just +=1)
    def increment_attempt(self, task_id: str):
        """Increment attempt counter (convenience for +=1)."""
        self.attempts[task_id] += 1
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "status": dict(self.status),
            "attempts": dict(self.attempts),
            "results": self.results.copy()
        }
