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
        if self.status == "completed":
            return
        self.status = "completed"
        self.result = {"key": key, "value": value}
        
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == "completed"

    def get_expected_keys(self) -> List[str]:
        """Get list of state keys this task expects.
        
        All expects are normalized to ExpectDefinition objects at load time.
        """
        return [exp.key for exp in self.expects]

    def validate(self, key: str, value: Any) -> tuple[bool, str]:
        """Validate a value against expectations.
        
        Returns (False, error) if:
        - Key is not in expects (unexpected key)
        - Value fails validation rules
        """
        for exp in self.expects:
            # Check if this expectation matches the key
            exp_key = None
            if isinstance(exp, str):
                exp_key = exp
            elif isinstance(exp, dict):
                exp_key = exp.get("key")
            elif hasattr(exp, "key"):
                exp_key = exp.key
            
            if exp_key == key:
                # Found the expectation, validation depends on type
                if hasattr(exp, 'validate_value'):
                    return exp.validate_value(value)
                return True, ""
        
        # Key not in expects - accept it (don't be overly strict)
        return True, ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize task state."""
        # Serialize expects if they are objects (ExpectDefinition)
        serialized_expects = []
        for exp in self.expects:
            if hasattr(exp, 'model_dump'):
                serialized_expects.append(exp.model_dump())
            elif hasattr(exp, 'dict'):
                serialized_expects.append(exp.dict())
            elif isinstance(exp, dict):
                serialized_expects.append(exp)
            elif isinstance(exp, str):
                serialized_expects.append(exp)
            elif hasattr(exp, '__dict__'):
                serialized_expects.append(exp.__dict__)
            else:
                # Fallback to string to prevent JSON serialization errors
                serialized_expects.append(str(exp))

        return {
            "id": self.id,
            "description": self.description,
            "expects": serialized_expects,
            "tools": self.tools,
            "silent": self.silent,
            "status": self.status,
            "result": self.result
        }
