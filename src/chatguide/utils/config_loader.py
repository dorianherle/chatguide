"""Config loader - parses YAML configuration files."""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from ..schemas import TaskDefinition
from ..adjustments import Adjustment


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
        
        # Convert shorthand actions to full format
        formatted_actions = []
        for action in actions:
            if isinstance(action, str):
                # Parse shorthand like "plan.remove_block(1)"
                formatted_actions.append(_parse_action_string(action))
            elif isinstance(action, dict):
                formatted_actions.append(action)
        
        adjustments.append(Adjustment(name, condition, formatted_actions))
    
    return adjustments


def _parse_action_string(action_str: str) -> Dict[str, Any]:
    """Parse action strings like 'plan.remove_block(1)' or 'tone.set(["warm"])'."""
    import re
    
    # Match pattern: object.method(args)
    match = re.match(r'(\w+)\.(\w+)\((.*)\)', action_str)
    if not match:
        return {}
    
    obj, method, args_str = match.groups()
    action_type = f"{obj}.{method}"
    
    # Parse args
    result = {"type": action_type}
    
    if args_str:
        try:
            # Evaluate args safely
            args_str = args_str.strip()
            if args_str.startswith('[') or args_str.startswith('{'):
                # List or dict
                evaluated = eval(args_str, {"__builtins__": {}})
                if action_type == "tone.set":
                    result["tones"] = evaluated
                elif action_type in ["plan.insert_block", "plan.replace_block"]:
                    result["tasks"] = evaluated
            else:
                # Single value (usually index)
                result["index"] = int(args_str)
        except:
            pass
    
    return result


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
    guardrails = data.get("guardrails", [])
    if isinstance(guardrails, list):
        return "\n".join(f"- {g}" for g in guardrails)
    return str(guardrails)
