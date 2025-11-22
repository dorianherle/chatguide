"""ExecutionState - tracks conversation flow and progress."""

from typing import List, Dict, Any, Optional


class ExecutionState:
    """Tracks the current position in the conversation flow."""
    
    def __init__(self):
        self._current_task: Optional[str] = None
        self._completed: List[str] = []
        self._pending_tools: List[Dict[str, Any]] = []
        self._status: str = "idle"  # idle | processing | awaiting_input | complete
    
    @property
    def current_task(self) -> Optional[str]:
        """Get current task ID."""
        return self._current_task
    
    @current_task.setter
    def current_task(self, task_id: Optional[str]):
        """Set current task ID."""
        self._current_task = task_id
    
    @property
    def completed(self) -> List[str]:
        """Get list of completed task IDs."""
        return self._completed.copy()
    
    @property
    def status(self) -> str:
        """Get execution status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        """Set execution status."""
        self._status = value
    
    def mark_complete(self, task_id: str):
        """Mark a task as completed."""
        if task_id not in self._completed:
            self._completed.append(task_id)
    
    def is_completed(self, task_id: str) -> bool:
        """Check if a task is completed."""
        return task_id in self._completed
    
    def progress(self, total_tasks: int) -> Dict[str, Any]:
        """Calculate progress metrics."""
        completed_count = len(self._completed)
        percent = int((completed_count / total_tasks * 100)) if total_tasks > 0 else 0
        
        return {
            "completed": completed_count,
            "total": total_tasks,
            "percent": percent,
            "current_task": self._current_task
        }
    
    def add_pending_tool(self, tool: Dict[str, Any]):
        """Add a pending UI tool."""
        self._pending_tools.append(tool)
    
    def get_pending_tools(self) -> List[Dict[str, Any]]:
        """Get pending UI tools."""
        return self._pending_tools.copy()
    
    def clear_pending_tools(self):
        """Clear pending tools."""
        self._pending_tools = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Export execution state as dict."""
        return {
            "current_task": self._current_task,
            "completed": self._completed.copy(),
            "pending_tools": self._pending_tools.copy(),
            "status": self._status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionState":
        """Restore execution state from dict."""
        state = cls()
        state._current_task = data.get("current_task")
        state._completed = data.get("completed", [])
        state._pending_tools = data.get("pending_tools", [])
        state._status = data.get("status", "idle")
        return state
