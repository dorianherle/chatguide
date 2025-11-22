"""State - flat dictionary with template resolution and audit tracking."""

import re
from typing import Any, Dict, Optional

# Avoid circular import - audit will be injected
if False:
    from .core.audit import AuditLog


class State:
    """Flat state dictionary with template resolution and audit tracking.
    
    Central working memory for all variables and outputs.
    Supports Pythonic attribute access: state.user_name instead of state.get("user_name")
    """
    
    def __init__(self, initial: Dict[str, Any] = None, audit_log: Optional["AuditLog"] = None):
        # Use object.__setattr__ to avoid triggering our custom __setattr__
        object.__setattr__(self, '_data', initial or {})
        object.__setattr__(self, '_audit_log', audit_log)
    
    def get(self, key: str, default=None) -> Any:
        """Get value from state."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any, source_task: Optional[str] = None):
        """Set value in state with optional audit logging."""
        old_value = self._data.get(key)
        self._data[key] = value
        
        # Log change if audit is enabled
        if self._audit_log and old_value != value:
            self._audit_log.log(key, old_value, value, source_task)
    
    def update(self, data: Dict[str, Any], source_task: Optional[str] = None):
        """Update state with dictionary."""
        for key, value in data.items():
            self.set(key, value, source_task)

    def get_typed(self, key: str, type_: type, default=None) -> Any:
        """Get value with type checking."""
        val = self._data.get(key, default)
        if val is not None and not isinstance(val, type_):
            try:
                return type_(val)
            except (ValueError, TypeError):
                return default
        return val
    
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
    
    @property
    def variables(self) -> Dict[str, Any]:
        """Get clean dict of all variables (business data only)."""
        return self._data.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export state as dict."""
        return self._data.copy()
    
    def __contains__(self, key: str) -> bool:
        """Support 'key in state' syntax."""
        return key in self._data
    
    def __getattr__(self, name: str) -> Any:
        """Support state.variable_name syntax for reading."""
        if name.startswith('_'):
            # Avoid infinite recursion for private attributes
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return self._data.get(name)
    
    def __setattr__(self, name: str, value: Any):
        """Support state.variable_name = value syntax for writing."""
        if name.startswith('_'):
            # Private attributes go to __dict__
            object.__setattr__(self, name, value)
        else:
            # Public attributes go to _data with audit logging
            self.set(name, value)
    
    def __repr__(self):
        return f"State({self._data})"

