"""Tools - simple tool executor."""

from typing import Dict, Any, Optional, Callable


class ToolDefinition:
    """Tool definition with metadata."""
    
    def __init__(self, tool_id: str, type: str, description: str, handler: Optional[Callable] = None):
        self.tool_id = tool_id
        self.type = type
        self.description = description
        self.handler = handler


class ToolRegistry:
    """Registry of available tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool_id: str, type: str, description: str, handler: Optional[Callable] = None):
        """Register a tool."""
        self._tools[tool_id] = ToolDefinition(tool_id, type, description, handler)
    
    def get(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id)
    
    def to_dict(self) -> dict:
        return {tid: {"type": t.type, "description": t.description} for tid, t in self._tools.items()}


class ToolExecutor:
    """Simple sync tool executor."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    def execute(self, tool_id: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a tool. Returns dict to merge into state, or None."""
        tool = self.registry.get(tool_id)
        if not tool or not tool.handler:
            return None
        
        result = tool.handler(**args)
        return result if isinstance(result, dict) else None


# Global registry
_global_registry = ToolRegistry()


def register_tool(tool_id: str, type: str, description: str, handler: Optional[Callable] = None):
    """Register a tool in global registry."""
    _global_registry.register(tool_id, type, description, handler)


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    return _global_registry
