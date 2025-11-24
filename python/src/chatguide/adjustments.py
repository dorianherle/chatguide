"""Adjustments - reactive rules that monitor state and modify plan/tone/state."""

from typing import List, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .state import State
    from .plan import Plan


class Adjustment:
    """Single adjustment rule."""
    
    def __init__(self, name: str, condition: str, actions: List[Dict[str, Any]]):
        self.name = name
        self.condition = condition
        self.actions = actions
        self.fired = False
    
    def reset(self):
        """Reset fired flag."""
        self.fired = False


class Adjustments:
    """Adjustment evaluation engine.
    
    Reactive rules watching state and mutating plan/tone/state.
    """
    
    def __init__(self, adjustments: List[Adjustment] = None):
        self._adjustments = adjustments or []
    
    def add(self, adjustment: Adjustment):
        """Add adjustment rule."""
        self._adjustments.append(adjustment)
    
    def evaluate(self, state: "State", plan: "Plan", tone: List[str]) -> List[str]:
        """Evaluate all adjustments and execute matching ones.
        
        Returns list of adjustment names that fired.
        """
        fired_names = []
        
        for adj in self._adjustments:
            if adj.fired:
                continue
            
            # Build evaluation context
            context = {
                "state": state._data,
                "plan": plan,
                "tone": tone,
                "__builtins__": {}
            }
            
            # Evaluate condition
            try:
                if eval(adj.condition, context):
                    self._execute_actions(adj.actions, state, plan, tone)
                    adj.fired = True
                    fired_names.append(adj.name)
            except Exception as e:
                # Silently skip invalid conditions
                pass
        
        return fired_names
    
    def _execute_actions(self, actions: List[Dict[str, Any]], state: "State", 
                        plan: "Plan", tone: List[str]):
        """Execute adjustment actions."""
        for action in actions:
            action_type = action.get("type")
            
            if action_type == "plan.insert_block":
                index = action.get("index", 0)
                tasks = action.get("tasks", [])
                plan.insert_block(index, tasks)
            
            elif action_type == "plan.remove_block":
                index = action.get("index", 0)
                plan.remove_block(index)
            
            elif action_type == "plan.replace_block":
                index = action.get("index", 0)
                tasks = action.get("tasks", [])
                plan.replace_block(index, tasks)
            
            elif action_type == "plan.jump_to":
                index = action.get("index", 0)
                plan.jump_to(index)
            
            elif action_type == "tone.set":
                new_tones = action.get("tones", [])
                tone.clear()
                tone.extend(new_tones)
            
            elif action_type == "tone.add":
                new_tone = action.get("tone")
                if new_tone and new_tone not in tone:
                    tone.append(new_tone)
            
            elif action_type == "state.set":
                key = action.get("key")
                value = action.get("value")
                if key:
                    state.set(key, value)
    
    def reset_all(self):
        """Reset all fired flags."""
        for adj in self._adjustments:
            adj.reset()
    
    def to_dict(self) -> dict:
        """Export adjustments as dict."""
        return {
            "adjustments": [
                {
                    "name": adj.name,
                    "condition": adj.condition,
                    "fired": adj.fired
                }
                for adj in self._adjustments
            ]
        }

