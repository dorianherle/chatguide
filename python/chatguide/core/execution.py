from enum import Enum
from typing import Dict, Any, Optional, Union

class ExecStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    # Legacy 'awaiting_input' map to WAITING_USER? Or just use awaiting_input as value?
    # Checklist said: WAITING_USER. I'll use that but support alias.
    WAITING_USER = "awaiting_input" 
    WAITING_TOOL = "waiting_tool"
    COMPLETE = "complete"
    ERROR = "error"

class ExecutionState:
    """Tracks the current position in the conversation flow.
    
    Note: Pending UI tools are managed by ToolExecutor (single source of truth).
    """
    
    def __init__(self):
        self._current_task: Optional[str] = None
        self._status: ExecStatus = ExecStatus.IDLE
    
    @property
    def current_task(self) -> Optional[str]:
        """Get current task ID."""
        return self._current_task
    
    @current_task.setter
    def current_task(self, task_id: Optional[str]):
        """Set current task ID."""
        self._current_task = task_id
    
    @property
    def status(self) -> str:
        """Get execution status."""
        return self._status.value
    
    @status.setter
    def status(self, value: Union[str, ExecStatus]):
        """Set execution status."""
        # Only enforce strict transitions in debug mode
        if self._status == ExecStatus.COMPLETE and value != ExecStatus.COMPLETE:
            if __debug__:
                raise ValueError("Cannot transition from COMPLETE")
            return  # Silently ignore in production
        
        if isinstance(value, ExecStatus):
            self._status = value
            return
            
        try:
            self._status = ExecStatus(value)
        except ValueError:
            # Handle legacy/check list divergence
            if value == "waiting_user":
                self._status = ExecStatus.WAITING_USER
            else:
                if __debug__:
                    raise ValueError(f"Invalid status: {value}")
                # Silently ignore invalid status in production
    
    def progress(self, completed_count: int, total_tasks: int) -> Dict[str, Any]:
        """Calculate progress metrics."""
        percent = int((completed_count / total_tasks * 100)) if total_tasks > 0 else 0
        
        return {
            "completed": completed_count,
            "total": total_tasks,
            "percent": percent,
            "current_task": self._current_task
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export execution state as dict."""
        return {
            "current_task": self._current_task,
            "status": self._status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionState":
        """Restore execution state from dict."""
        state = cls()
        state._current_task = data.get("current_task")
        # Ignore pending_tools from old checkpoints (ephemeral UI state)
        state.status = data.get("status", "idle")
        return state
