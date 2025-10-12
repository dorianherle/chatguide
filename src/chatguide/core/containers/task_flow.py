"""Task flow container - manages batches and navigation."""

from typing import List


class TaskFlow:
    """Task batches and navigation.
    
    All attributes are directly editable:
        flow.batches[0] = ["new_task"]
        flow.persistent.append("monitor")
        flow.current_index = 2
    """
    
    def __init__(self, debug: bool = False):
        self.batches: List[List[str]] = []
        self.persistent: List[str] = []
        self.current_index: int = 0
        self.debug = debug
    
    # Initialization
    def set_flow(self, batches: List[List[str]], persistent: List[str] = None):
        """Initialize flow (convenience for setup)."""
        self.batches = batches
        self.persistent = persistent or []
        self.current_index = 0
    
    # Convenience methods (with logic)
    def get_current_batch(self) -> List[str]:
        """Get current batch tasks."""
        if self.current_index >= len(self.batches):
            return []
        return self.batches[self.current_index]
    
    def get_next_batch(self) -> List[str]:
        """Get next batch."""
        next_idx = self.current_index + 1
        if next_idx < len(self.batches):
            return self.batches[next_idx]
        return []
    
    def advance(self, force: bool = False, target: int = None):
        """Advance to next batch or jump to target.
        
        Has logic for bounds checking and validation.
        """
        if target is not None:
            if 0 <= target <= len(self.batches):
                self.current_index = target
                if self.debug:
                    print(f"Jumped to batch {target}")
            else:
                if self.debug:
                    print(f"Invalid target: {target}")
                return False
        else:
            self.current_index += 1
            if self.debug:
                print(f"Advanced to batch {self.current_index}")
        return True
    
    def is_finished(self) -> bool:
        """Check if past last batch."""
        return self.current_index >= len(self.batches)
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "batches": [b.copy() for b in self.batches],
            "persistent": self.persistent.copy(),
            "current_index": self.current_index,
            "is_finished": self.is_finished()
        }
