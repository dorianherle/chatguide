"""Conversation state - assembles all containers."""

from .containers.flow import Flow
from .containers.tasks import Tasks
from .containers.conversation import Conversation
from .containers.tones import Tones
from .containers.routes import Routes
from .containers.participants import Participants
from typing import List


class ConversationState:
    """Main state container holding all conversation state.
    
    This is the single source of truth for everything that changes
    during a conversation.
    """
    
    def __init__(self, debug: bool = False):
        # Sub-containers
        self.flow = Flow(debug=debug)
        self.tasks = Tasks()
        self.conversation = Conversation()
        self.tones = Tones()
        self.routes = Routes()
        self.participants = Participants()
        
        # Language
        self.language = "en"  # ISO 639-1 code
        
        self.debug = debug
    
    # Convenience helpers (common queries)
    def get_current_tasks(self) -> List[str]:
        """Get incomplete tasks from current batch."""
        current_batch = self.flow.get_current_batch()
        return [t for t in current_batch 
                if self.tasks.status.get(t) != "completed"]
    
    def get_persistent_tasks(self) -> List[str]:
        """Get active persistent tasks."""
        return [t for t in self.flow.persistent 
                if self.tasks.status.get(t) == "active"]
    
    def is_finished(self) -> bool:
        """Check if conversation is complete."""
        return self.flow.is_finished()
    
    # Serialization
    def to_dict(self) -> dict:
        """Export full state as dict."""
        return {
            # Container data
            "flow": self.flow.to_dict(),
            "tasks": self.tasks.to_dict(),
            "conversation": self.conversation.to_dict(),
            "tones": self.tones.to_dict(),
            "routes": self.routes.to_dict(),
            "participants": self.participants.to_dict(),
            
            # Language
            "language": self.language,
            
            # Convenience fields (for debugging/display)
            "current_tasks": self.get_current_tasks(),
            "persistent_tasks": self.get_persistent_tasks(),
        }
