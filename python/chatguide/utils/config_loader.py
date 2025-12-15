"""Config loader - parses YAML configuration files."""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from ..schemas import TaskDefinition
from ..adjustments import (
    Adjustment, Action, PlanJump, PlanInsertBlock, PlanRemoveBlock, 
    PlanReplaceBlock, ToneSet, ToneAdd, StateSet
)


def load_config_file(path: str) -> dict:
    """Load YAML config file."""
    config_path = Path(path)
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def parse_state(data: dict) -> Dict[str, Any]:
    """Parse initial state from config."""
    return data.get("state", {})


def parse_plan(data: dict) -> List[List[str]]:
    """Parse plan (task blocks) from config."""
    return data.get("plan", [])


def parse_tasks(data: dict) -> Dict[str, TaskDefinition]:
    """Parse task definitions from config."""
    tasks = {}
    for task_id, task_data in data.get("tasks", {}).items():
        tasks[task_id] = TaskDefinition(
            description=task_data.get("description", ""),
            expects=task_data.get("expects", []),
            tools=task_data.get("tools", []),
            silent=task_data.get("silent", False)
        )
    return tasks


def parse_tools(data: dict) -> Dict[str, Dict[str, Any]]:
    """Parse tool definitions from config."""
    return data.get("tools", {})


def parse_adjustments(data: dict) -> List[Adjustment]:
    """Parse adjustments from config."""
    adjustments = []
    for adj_data in data.get("adjustments", []):
        name = adj_data.get("name", "unnamed")
        condition = adj_data.get("when", "False")
        actions = adj_data.get("actions", [])
        
        # Convert actions to full format / objects
        formatted_actions = []
        for action in actions:
            if isinstance(action, str):
                # Parse shorthand like "plan.remove_block(1)"
                obj = _parse_action_string(action)
                if obj:
                    formatted_actions.append(obj)
            elif isinstance(action, dict):
                formatted_actions.append(_dict_to_action(action))
        
        adjustments.append(Adjustment(name, condition, formatted_actions))
    
    return adjustments


def _dict_to_action(d: Dict[str, Any]) -> Any:
    """Convert dict action to Action object."""
    t = d.get("type")
    if t == "plan.jump_to":
        return PlanJump(index=d.get("index", 0))
    elif t == "plan.remove_block":
        return PlanRemoveBlock(index=d.get("index", 0))
    elif t == "plan.insert_block":
        return PlanInsertBlock(index=d.get("index", 0), tasks=d.get("tasks", []))
    elif t == "plan.replace_block":
        return PlanReplaceBlock(index=d.get("index", 0), tasks=d.get("tasks", []))
    elif t == "tone.set":
        return ToneSet(tones=d.get("tones", []))
    elif t == "tone.add":
        return ToneAdd(tone=d.get("tone", ""))
    elif t == "state.set":
        return StateSet(key=d.get("key", ""), value=d.get("value"))
    return d


def _parse_action_string(action_str: str) -> Any:
    """Parse action strings like 'plan.remove_block(1)' into Action objects."""
    import re
    import ast
    
    # Match pattern: object.method(args)
    match = re.match(r'(\w+)\.(\w+)\((.*)\)', action_str)
    if not match:
        return None
    
    obj, method, args_str = match.groups()
    action_type = f"{obj}.{method}"
    
    # Parse args
    args = {}
    if args_str:
        try:
            # Evaluate args safely
            args_str = args_str.strip()
            if args_str.startswith('[') or args_str.startswith('{'):
                # List or dict
                evaluated = ast.literal_eval(args_str)
                if action_type == "tone.set":
                    args["tones"] = evaluated
                elif action_type in ["plan.insert_block", "plan.replace_block"]:
                    args["tasks"] = evaluated
            else:
                # Single value (usually index)
                args["index"] = int(args_str)
        except Exception as e:
            if __debug__:
                raise ValueError(f"Invalid adjustment action: {action_str}") from e
            # Silently ignore in production
    
    # Construct object
    if action_type == "plan.jump_to":
        return PlanJump(index=args.get("index", 0))
    elif action_type == "plan.remove_block":
        return PlanRemoveBlock(index=args.get("index", 0))
    elif action_type == "plan.insert_block":
        return PlanInsertBlock(index=args.get("index", 0), tasks=args.get("tasks", []))
    elif action_type == "plan.replace_block":
        return PlanReplaceBlock(index=args.get("index", 0), tasks=args.get("tasks", []))
    elif action_type == "tone.set":
        return ToneSet(tones=args.get("tones", []))
    elif action_type == "tone.add":
        # Argument for tone.add("warm") is strictly a string, not index
        # But regex parsing put it in 'args_str'. 
        # For 'tone.add("warm")', eval would return "warm".
        # Let's fix eval usage for single string
        if args_str and (args_str.startswith('"') or args_str.startswith("'")):
             try:
                 val = ast.literal_eval(args_str)
                 return ToneAdd(tone=val)
             except:
                 pass
        return ToneAdd(tone=args_str) # Fallback
    
    return {"type": action_type, **args} # Fallback legacy dict


def parse_tone(data: dict) -> List[str]:
    """Parse initial tone from config."""
    return data.get("tone", [])


def parse_tones(data: dict) -> Dict[str, str]:
    """Parse tone definitions from config."""
    tones = {}
    for tone_id, tone_data in data.get("tones", {}).items():
        if isinstance(tone_data, dict):
            tones[tone_id] = tone_data.get("description", "")
        else:
            tones[tone_id] = tone_data
    return tones


def parse_guardrails(data: dict) -> str:
    """Parse guardrails from config."""
    guardrails = data.get("guardrails", {})
    if isinstance(guardrails, list):
        return "\n".join(f"- {g}" for g in guardrails)
    elif isinstance(guardrails, dict):
        # Format as key: value pairs
        return "\n".join(f"- {key}: {value}" for key, value in guardrails.items())
    return str(guardrails)
