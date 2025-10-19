"""ChatGuide - State-driven conversational agent framework."""

from .chatguide import ChatGuide
from .state import State
from .plan import Plan
from .adjustments import Adjustments, Adjustment
from .tool_executor import register_tool, get_tool_registry
from .schemas import ChatGuideReply, TaskDefinition, ToolCall, TaskResult

# Register built-in HTML tools
register_tool(
    "html.button_choice",
    "ui",
    "Display clickable button options for user to choose from"
)

register_tool(
    "html.card_swipe",
    "ui",
    "Display animated credit card swipe for payment processing"
)

__all__ = [
    "ChatGuide",
    "State",
    "Plan",
    "Adjustments",
    "Adjustment",
    "register_tool",
    "get_tool_registry",
    "ChatGuideReply",
    "TaskDefinition",
    "ToolCall",
    "TaskResult"
]
