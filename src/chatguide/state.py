"""State - flat dictionary with template resolution."""

import re
from typing import Any, Dict


class State:
    """Flat state dictionary with template resolution.
    
    Central working memory for all variables and outputs.
    """
    
    def __init__(self, initial: Dict[str, Any] = None):
        self._data: Dict[str, Any] = initial or {}
    
    def get(self, key: str, default=None) -> Any:
        """Get value from state."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set value in state."""
        self._data[key] = value
    
    def update(self, data: Dict[str, Any]):
        """Update state with dictionary."""
        self._data.update(data)
    
    def resolve_template(self, template: Any) -> Any:
        """Resolve {{var}} templates in strings, dicts, or lists.
        
        Examples:
            "Hello {{user_name}}" -> "Hello John"
            {"name": "{{user_name}}"} -> {"name": "John"}
            ["{{var1}}", "{{var2}}"] -> ["value1", "value2"]
        """
        if isinstance(template, str):
            return self._resolve_string(template)
        elif isinstance(template, dict):
            return {k: self.resolve_template(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.resolve_template(item) for item in template]
        return template
    
    def _resolve_string(self, text: str) -> str:
        """Resolve {{var}} patterns in string."""
        pattern = r'\{\{(\w+)\}\}'
        
        def replacer(match):
            var_name = match.group(1)
            value = self._data.get(var_name)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(pattern, replacer, text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export state as dict."""
        return self._data.copy()
    
    def __repr__(self):
        return f"State({self._data})"

