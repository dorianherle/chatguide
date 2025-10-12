"""Configuration container - immutable definitions."""

from typing import Dict
from ..schemas import Task


class Config:
    """Holds task definitions, tones, and guardrails."""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.tones: Dict[str, str] = {}
        self.guardrails: str = ""
    
    def add_task(self, key: str, description: str):
        """Add task definition."""
        self.tasks[key] = Task(key=key, description=description)
    
    def get_task_description(self, task_id: str) -> str:
        """Get task description."""
        if task_id in self.tasks:
            return self.tasks[task_id].description
        return "Unknown"
    
    def to_dict(self) -> dict:
        return {
            "tasks": {k: v.description for k, v in self.tasks.items()},
            "tones": self.tones.copy(),
            "guardrails": self.guardrails
        }
