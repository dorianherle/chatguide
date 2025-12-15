"""Pydantic schemas for ChatGuide."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union


class ExpectDefinition(BaseModel):
    """Definition for an expected value with optional validation.
    
    Only use for:
    - Numbers with min/max range (e.g., age: 1-120)
    - Enums with specific choices (e.g., mood: happy/sad/neutral)
    
    For plain strings, just use the key name directly: expects: [user_name]
    """
    key: str
    type: str = "string"  # number, enum (string is default, no validation)
    min: Optional[float] = None  # For numbers: minimum value
    max: Optional[float] = None  # For numbers: maximum value
    choices: Optional[List[str]] = None  # For enums: valid choices
    confirm: bool = False  # If true, requires explicit confirmation flag in state
    
    def validate_value(self, value: str) -> tuple[bool, str]:
        """Validate a value against this definition. Returns (is_valid, error_message)."""
        if self.type == "number":
            try:
                num = float(value)
                if self.min is not None and num < self.min:
                    return False, f"Value {num} is below minimum {self.min}"
                if self.max is not None and num > self.max:
                    return False, f"Value {num} is above maximum {self.max}"
            except ValueError:
                return False, f"'{value}' is not a valid number"
        elif self.type == "enum":
            if self.choices and value.lower() not in [c.lower() for c in self.choices]:
                return False, f"Value must be one of: {', '.join(self.choices)}"
        return True, ""


class TaskDefinition(BaseModel):
    """Task definition from config."""
    description: str
    expects: List[Union[str, ExpectDefinition]] = []
    tools: List[Dict[str, Any]] = []
    silent: bool = False  # If True, don't show assistant_reply (just collect state)
    
    def get_expect_keys(self) -> List[str]:
        """Get just the keys from expects (handles both string and ExpectDefinition)."""
        keys = []
        for exp in self.expects:
            if isinstance(exp, str):
                keys.append(exp)
            else:
                keys.append(exp.key)
        return keys
    
    def get_expect_definition(self, key: str) -> Optional[ExpectDefinition]:
        """Get the ExpectDefinition for a key, or None if it's just a string."""
        for exp in self.expects:
            if isinstance(exp, ExpectDefinition) and exp.key == key:
                return exp
        return None
    
    def validate_value(self, key: str, value: str) -> tuple[bool, str]:
        """Validate a value for a given key. Returns (is_valid, error_message)."""
        exp_def = self.get_expect_definition(key)
        if exp_def:
            return exp_def.validate_value(value)
        return True, ""  # No validation defined


class ToolCall(BaseModel):
    """Tool invocation from LLM."""
    tool: str
    options: Optional[List[str]] = None


class TaskResult(BaseModel):
    """Task execution result from LLM."""
    task_id: str = ""  # Which task this result belongs to (optional for backwards compat)
    key: str
    value: str



class ChatGuideReply(BaseModel):
    """LLM response envelope."""
    assistant_reply: str
    task_results: List[TaskResult] = []
    tools: List[ToolCall] = []
    
    @property
    def text(self) -> str:
        """Alias for assistant_reply (shorter, more intuitive)."""
        return self.assistant_reply
