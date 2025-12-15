"""Context - manages conversation history and session metadata."""

from typing import List, Dict, Any, Optional
from datetime import datetime


class Message:
    """Represents a single message in the conversation."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


class Context:
    """Manages conversation history and session metadata."""
    
    def __init__(self, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self.metadata = metadata or {}
        self._history: List[Message] = []
        self.created_at = datetime.now().isoformat()
    
    @property
    def history(self) -> List[Message]:
        """Get conversation history."""
        return self._history
    
    def add_message(self, role: str, content: str):
        """Add a message to history."""
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'.")
        self._history.append(Message(role, content))
    
    def get_history_dict(self) -> List[Dict[str, str]]:
        """Get history as list of dicts (for LLM prompts)."""
        return [{"role": msg.role, "content": msg.content} for msg in self._history]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export context as dict."""
        return {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "history": [msg.to_dict() for msg in self._history],
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        """Restore context from dict."""
        ctx = cls(session_id=data.get("session_id"), metadata=data.get("metadata", {}))
        ctx.created_at = data.get("created_at", datetime.now().isoformat())
        
        for msg_data in data.get("history", []):
            ctx._history.append(Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=msg_data.get("timestamp")
            ))
        
        return ctx
