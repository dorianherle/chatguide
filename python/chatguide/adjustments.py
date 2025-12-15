"""Adjustments - reactive rules that monitor state and modify plan/tone/state."""

import logging
import re
from typing import List, Dict, Any, Callable, Union, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .state import State
    from .plan import Plan
else:
    from .core.block import Block
    from .core.task import Task


logger = logging.getLogger(__name__)


class Adjustment:
    """Single adjustment rule with safe condition evaluation."""
    
    def __init__(
        self, 
        name: str, 
        condition: Union[Dict[str, Any], bool], 
        actions: List[Dict[str, Any]]
    ):
        self.name = name
        self.condition = condition
        self.actions = actions
        self.fired = False
    
    def reset(self):
        """Reset fired flag."""
        self.fired = False
    
    def evaluate_condition(self, state: "State", plan: "Plan", tone: List[str]) -> bool:
        """Evaluate condition using declarative AST."""
        if isinstance(self.condition, bool):
            return self.condition
            
        if isinstance(self.condition, dict):
            return self._eval_condition(self.condition, state, plan, tone)
            
        return False
    
    def _eval_condition(self, cond: Dict[str, Any], state: "State", plan: "Plan", tone: List[str]) -> bool:
        """Recursive AST evaluator."""
        # Logic operators
        if "all" in cond:
            return all(self._eval_condition(c, state, plan, tone) for c in cond["all"])
        if "any" in cond:
            return any(self._eval_condition(c, state, plan, tone) for c in cond["any"])
        if "not" in cond:
            return not self._eval_condition(cond["not"], state, plan, tone)
            
        # Leaf operators
        if "has" in cond:
            return state.get(cond["has"]) is not None
        
        if "eq" in cond:
            actual = state.get(cond["eq"]["key"])
            expected = cond["eq"]["value"]
            return actual == expected
            
        if "gt" in cond:
            val = float(state.get(cond["gt"]["key"], 0))
            return val > cond["gt"]["value"]
            
        return False


@dataclass
class Action:
    """Base class for adjustment actions."""
    pass

@dataclass
class PlanJump(Action):
    index: int

@dataclass
class PlanInsertBlock(Action):
    index: int
    tasks: List[str]

@dataclass
class PlanRemoveBlock(Action):
    index: int

@dataclass
class PlanReplaceBlock(Action):
    index: int
    tasks: List[str]

@dataclass
class ToneSet(Action):
    tones: List[str]

@dataclass
class ToneAdd(Action):
    tone: str

@dataclass
class StateSet(Action):
    key: str
    value: Any

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
            
            try:
                if adj.evaluate_condition(state, plan, tone):
                    self._execute_actions(adj.actions, state, plan, tone)
                    adj.fired = True
                    fired_names.append(adj.name)
            except Exception as e:
                # Log the error instead of silently swallowing
                logger.warning(f"Adjustment '{adj.name}' condition evaluation failed: {e}")
        
        return fired_names
    
    def _execute_actions(self, actions: List[Union[Dict[str, Any], Action]], state: "State", 
                        plan: "Plan", tone: List[str]):
        """Execute adjustment actions."""
        for action in actions:
            # Handle legacy dict actions (for backward compat if needed)
            if isinstance(action, dict):
                 # Convert to object (simplified) or execute old logic
                 # For cleanliness, we'll try to execute logic directly here if it's a dict
                 action_type = action.get("type")
                 index = action.get("index", 0)
                 task_ids = action.get("tasks", [])
                 
                 if action_type == "plan.insert_block":
                     tasks = [Task(id=tid, description="") for tid in task_ids]
                     plan.insert_block(index, Block(tasks))
                 elif action_type == "plan.remove_block":
                     plan.remove_block(index)
                 elif action_type == "plan.replace_block":
                     tasks = [Task(id=tid, description="") for tid in task_ids]
                     plan.replace_block(index, Block(tasks))
                 elif action_type == "plan.jump_to":
                     plan.jump_to(index)
                 elif action_type == "tone.set":
                     tone.clear()
                     tone.extend(action.get("tones", []))
                 return # Skip rest

            # Handle Typed Actions
            if isinstance(action, PlanInsertBlock):
                tasks = [Task(id=tid, description="") for tid in action.tasks]
                plan.insert_block(action.index, Block(tasks))
            
            elif isinstance(action, PlanRemoveBlock):
                plan.remove_block(action.index)
            
            elif isinstance(action, PlanReplaceBlock):
                tasks = [Task(id=tid, description="") for tid in action.tasks]
                plan.replace_block(action.index, Block(tasks))
            
            elif isinstance(action, PlanJump):
                plan.jump_to(action.index)
            
            elif isinstance(action, ToneSet):
                tone.clear()
                tone.extend(action.tones)
            
            elif isinstance(action, ToneAdd):
                if action.tone and action.tone not in tone:
                    tone.append(action.tone)
            
            elif isinstance(action, StateSet):
                if action.key:
                    state.set(action.key, action.value)
    
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
