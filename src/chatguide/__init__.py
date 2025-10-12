"""ChatGuide - The lightweight framework for guided conversational AI."""

__version__ = "2.0.0"

from .schemas import Task, TaskResult, ChatGuideReply
from .core.state import ConversationState
from .chatguide import ChatGuide
from .utils.debug_formatter import DebugFormatter

__all__ = [
    "ChatGuide",
    "ConversationState",
    "Task",
    "TaskResult",
    "ChatGuideReply",
    "DebugFormatter",
]
