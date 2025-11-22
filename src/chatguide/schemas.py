"""Pydantic schemas for ChatGuide."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class TaskDefinition(BaseModel):
    """Task definition from config."""
    description: str
    expects: List[str] = []
    tools: List[Dict[str, Any]] = []
    silent: bool = False  # If True, don't show assistant_reply (just collect state)


class ToolCall(BaseModel):
    """Tool invocation from LLM."""
    tool: str
    options: Optional[List[str]] = None


class TaskResult(BaseModel):
    """Task execution result from LLM."""
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
