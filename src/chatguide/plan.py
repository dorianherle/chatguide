"""Plan - ordered sequence of task blocks with manipulation methods."""

from typing import List, Optional
from .core.block import Block
from .core.task import Task

class Plan:
    """Ordered list of task blocks defining execution flow.
    
    Manages a sequence of Block objects.
    """
    
    def __init__(self, blocks: List[Block] = None):
        self._blocks: List[Block] = blocks or []
        self._current_index = 0
    
    def get_current_block(self) -> Optional[Block]:
        """Get current task block."""
        if self._current_index < len(self._blocks):
            return self._blocks[self._current_index]
        return None
    
    def get_block(self, index: int) -> Optional[Block]:
        """Get task block at index."""
        if 0 <= index < len(self._blocks):
            return self._blocks[index]
        return None
    
    def advance(self):
        """Move to next block."""
        if self._current_index < len(self._blocks):
            self._current_index += 1
    
    def jump_to(self, index: int):
        """Jump to specific block."""
        if 0 <= index < len(self._blocks):
            self._current_index = index
    
    def insert_block(self, index: int, block: Block):
        """Insert task block at index."""
        self._blocks.insert(index, block)
    
    def remove_block(self, index: int):
        """Remove block at index."""
        if 0 <= index < len(self._blocks):
            self._blocks.pop(index)
    
    def replace_block(self, index: int, block: Block):
        """Replace block at index."""
        if 0 <= index < len(self._blocks):
            self._blocks[index] = block
            
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks in the plan."""
        tasks = []
        for block in self._blocks:
            tasks.extend(block.tasks)
        return tasks
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """Find a task by ID anywhere in the plan."""
        for block in self._blocks:
            task = block.get_task(task_id)
            if task:
                return task
        return None
    
    def is_finished(self) -> bool:
        """Check if plan is complete."""
        return self._current_index >= len(self._blocks)
    
    @property
    def current_index(self) -> int:
        """Get current block index."""
        return self._current_index
    
    def to_dict(self) -> dict:
        """Export plan as dict."""
        return {
            "blocks": [b.to_dict() for b in self._blocks],
            "current_index": self._current_index,
            "is_finished": self.is_finished()
        }
    
    def __repr__(self):
        return f"Plan(blocks={len(self._blocks)}, current={self._current_index})"

