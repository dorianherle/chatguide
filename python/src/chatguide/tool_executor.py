"""Tools - unified async tool executor."""

from typing import Dict, Any, Optional, Callable
import asyncio


class ToolDefinition:
    """Tool definition with metadata."""
    
    def __init__(self, tool_id: str, type: str, description: str, 
                 handler: Optional[Callable] = None):
        self.tool_id = tool_id
        self.type = type
        self.description = description
        self.handler = handler


class ToolRegistry:
    """Registry of available tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool_id: str, type: str, description: str, 
                handler: Optional[Callable] = None):
        """Register a tool."""
        self._tools[tool_id] = ToolDefinition(tool_id, type, description, handler)
    
    def get(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get tool definition."""
        return self._tools.get(tool_id)
    
    def get_all(self) -> Dict[str, ToolDefinition]:
        """Get all tools."""
        return self._tools.copy()
    
    def to_dict(self) -> dict:
        """Export tools as dict for prompts."""
        return {
            tool_id: {
                "type": tool.type,
                "description": tool.description
            }
            for tool_id, tool in self._tools.items()
        }


class ToolExecutor:
    """Unified async tool executor.
    
    Executes tools and writes results back to state.
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self._pending_ui_tools = []
    
    async def execute(self, tool_id: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a tool with resolved arguments.
        
        Returns dict to merge into state, or None.
        """
        tool = self.registry.get(tool_id)
        if not tool:
            return None
        
        # UI tools don't execute immediately - they're queued for rendering
        if tool.type == "ui":
            self._pending_ui_tools.append({
                "tool": tool_id,
                "args": args
            })
            return None
        
        # Function/API tools execute via handler
        if tool.handler:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**args)
            else:
                result = tool.handler(**args)
            
            # If handler returns dict, merge into state
            if isinstance(result, dict):
                return result
        
        return None
    
    def get_pending_ui_tools(self) -> list:
        """Get pending UI tools to render."""
        tools = self._pending_ui_tools.copy()
        self._pending_ui_tools.clear()
        return tools
    
    def has_pending_ui_tools(self) -> bool:
        """Check if there are pending UI tools."""
        return len(self._pending_ui_tools) > 0


# Global registry
_global_registry = ToolRegistry()


def register_tool(tool_id: str, type: str, description: str, 
                 handler: Optional[Callable] = None):
    """Register a tool in global registry."""
    _global_registry.register(tool_id, type, description, handler)


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    return _global_registry

