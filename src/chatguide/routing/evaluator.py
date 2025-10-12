"""Route condition evaluator."""

from typing import Dict, Any


class RouteEvaluator:
    """Safely evaluates route conditions."""
    
    @staticmethod
    def evaluate(condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate condition with given context."""
        if not condition:
            return False
        
        try:
            safe_context = {
                "__builtins__": {},
                "len": len,
                "max": max,
                "min": min,
                **context
            }
            return eval(condition, safe_context)
        except Exception:
            return False
