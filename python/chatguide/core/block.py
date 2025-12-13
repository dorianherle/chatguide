"""Block object representing a group of tasks."""

from typing import List, Dict, Any
from .task import Task

class Block:
    """Represents a group of tasks that can be executed together."""
    
    def __init__(self, tasks: List[Task]):
        self.tasks = tasks
        
    @property
    def task_ids(self) -> List[str]:
        """Get list of task IDs in this block."""
        return [t.id for t in self.tasks]
        
    def is_complete(self) -> bool:
        """Check if all tasks in block are complete."""
        return all(t.is_completed() for t in self.tasks)
        
    def get_pending_tasks(self) -> List[Task]:
        """Get tasks that are not yet completed."""
        return [t for t in self.tasks if not t.is_completed()]
        
    def get_task(self, task_id: str) -> Task:
        """Get task by ID if it exists in this block."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize block."""
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "status": "completed" if self.is_complete() else "pending"
        }
