"""Plan - ordered sequence of task blocks with manipulation methods."""

from typing import List


class Plan:
    """Ordered list of task blocks defining execution flow.
    
    Each block is a list of task names.
    """
    
    def __init__(self, blocks: List[List[str]] = None):
        self._blocks: List[List[str]] = blocks or []
        self._current_index = 0
    
    def get_current_block(self) -> List[str]:
        """Get current task block."""
        if self._current_index < len(self._blocks):
            return self._blocks[self._current_index]
        return []
    
    def get_block(self, index: int) -> List[str]:
        """Get task block at index."""
        if 0 <= index < len(self._blocks):
            return self._blocks[index]
        return []
    
    def advance(self):
        """Move to next block."""
        if self._current_index < len(self._blocks):
            self._current_index += 1
    
    def jump_to(self, index: int):
        """Jump to specific block."""
        if 0 <= index < len(self._blocks):
            self._current_index = index
    
    def insert_block(self, index: int, tasks: List[str]):
        """Insert task block at index."""
        self._blocks.insert(index, tasks)
    
    def remove_block(self, index: int):
        """Remove block at index."""
        if 0 <= index < len(self._blocks):
            self._blocks.pop(index)
    
    def replace_block(self, index: int, tasks: List[str]):
        """Replace block at index."""
        if 0 <= index < len(self._blocks):
            self._blocks[index] = tasks
    
    def insert_task(self, block_index: int, task: str, position: int = None):
        """Insert task into a block."""
        if 0 <= block_index < len(self._blocks):
            if position is None:
                self._blocks[block_index].append(task)
            else:
                self._blocks[block_index].insert(position, task)
    
    def remove_task(self, block_index: int, task: str):
        """Remove task from a block."""
        if 0 <= block_index < len(self._blocks):
            if task in self._blocks[block_index]:
                self._blocks[block_index].remove(task)
    
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
            "blocks": self._blocks,
            "current_index": self._current_index,
            "is_finished": self.is_finished()
        }
    
    def __repr__(self):
        return f"Plan(blocks={len(self._blocks)}, current={self._current_index})"

