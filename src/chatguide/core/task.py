"""Task object representing a unit of work."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Task:
    """Represents a single task in the conversation plan."""
    
    id: str
    description: str
    expects: List[str] = field(default_factory=list)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    silent: bool = False
    
    # Runtime state
    status: str = "pending"  # pending, in_progress, completed
    result: Optional[Dict[str, Any]] = None
    
    def complete(self, key: str, value: Any):
        """Mark task as complete with extracted value."""
        self.status = "completed"
        self.result = {"key": key, "value": value}
        
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize task state."""
        return {
            "id": self.id,
            "description": self.description,
            "expects": self.expects,
            "tools": self.tools,
            "silent": self.silent,
            "status": self.status,
            "result": self.result
        }
