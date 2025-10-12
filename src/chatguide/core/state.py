"""Conversation state - assembles all containers."""

from .containers.task_flow import TaskFlow
from .containers.task_tracker import TaskTracker
from .containers.conversation import Conversation
from .containers.interaction import Interaction
from .containers.participants import Participants
from typing import List


class ConversationState:
    """Main state container holding all conversation state.
    
    This is the single source of truth for everything that changes
    during a conversation.
    """
    
    def __init__(self, debug: bool = False):
        # Sub-containers
        self.flow = TaskFlow(debug=debug)
        self.tracker = TaskTracker()
        self.conversation = Conversation()
        self.interaction = Interaction()
        self.participants = Participants()
        
        self.debug = debug
    
    # Convenience helpers (common queries)
    def get_current_tasks(self) -> List[str]:
        """Get incomplete tasks from current batch."""
        current_batch = self.flow.get_current_batch()
        return [t for t in current_batch 
                if self.tracker.status.get(t) != "completed"]
    
    def get_persistent_tasks(self) -> List[str]:
        """Get active persistent tasks."""
        return [t for t in self.flow.persistent 
                if self.tracker.status.get(t) == "active"]
    
    def is_finished(self) -> bool:
        """Check if conversation is complete."""
        return self.flow.is_finished()
    
    # Serialization
    def to_dict(self) -> dict:
        """Export full state as dict."""
        return {
            # Container data
            "flow": self.flow.to_dict(),
            "tracker": self.tracker.to_dict(),
            "conversation": self.conversation.to_dict(),
            "interaction": self.interaction.to_dict(),
            "participants": self.participants.to_dict(),
            
            # Convenience fields (for debugging/display)
            "current_tasks": self.get_current_tasks(),
            "persistent_tasks": self.get_persistent_tasks(),
        }
