"""Conversation container - memory and history."""

from typing import List


class Conversation:
    """Manages memory and chat history.
    
    All attributes are directly editable:
        conversation.memory = "New context"
        conversation.history.append("User: hi")
        conversation.max_turns = 20
    """
    
    def __init__(self, max_turns: int = 10):
        self.memory: str = ""
        self.history: List[str] = []
        self.max_turns: int = max_turns
    
    # Method with logic (auto-trimming)
    def add_message(self, role: str, text: str):
        """Add message with automatic history trimming."""
        self.history.append(f"{role}: {text}")
        
        # Auto-trim
        max_messages = self.max_turns * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]
    
    def get_recent_history(self, turns: int = None) -> List[str]:
        """Get recent history (convenience)."""
        limit = (turns or self.max_turns) * 2
        return self.history[-limit:]
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "memory": self.memory,
            "history": self.history.copy(),
            "max_turns": self.max_turns
        }
