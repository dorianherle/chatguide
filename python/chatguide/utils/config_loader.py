"""Config loader - parses YAML configuration files."""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Union
from ..schemas import TaskDefinition, ExpectDefinition
from ..adjustments import (
    Adjustment, Action, PlanJump, PlanInsertBlock, PlanRemoveBlock,
    PlanReplaceBlock, ToneSet, ToneAdd, StateSet
)


def load_config_file(path: str) -> dict:
    """Load YAML config file with better error handling."""
    config_path = Path(path)
    try:
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file is empty
        if not content.strip():
            raise ValueError(f"Config file is empty: {path}")

        try:
            data = yaml.safe_load(content)
            if data is None:
                raise ValueError(f"Config file contains no valid YAML data: {path}")
            return data
        except yaml.YAMLError as e:
            line_info = ""
            if hasattr(e, 'problem_mark') and e.problem_mark:
                line_info = f" at line {e.problem_mark.line + 1}, column {e.problem_mark.column + 1}"
            raise ValueError(f"Invalid YAML syntax in config file '{path}'{line_info}: {e.problem}")

    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading config file: {path}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Config file encoding error in '{path}': {e}")
    except Exception as e:
        raise ValueError(f"Error loading config file '{path}': {e}")


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


def validate_config(data: dict) -> List[str]:
    """Validate config structure and return list of error messages."""
    errors = []

    # Validate plan
    plan = data.get("plan", [])
    if not isinstance(plan, list):
        errors.append("plan must be a list of task blocks")
    else:
        for i, block in enumerate(plan):
            if not isinstance(block, list):
                errors.append(f"plan[{i}] must be a list of task IDs")
            else:
                for j, task_id in enumerate(block):
                    if not isinstance(task_id, str):
                        errors.append(f"plan[{i}][{j}] must be a string task ID")

    # Validate tasks
    tasks = data.get("tasks", {})
    if not isinstance(tasks, dict):
        errors.append("tasks must be a dictionary")
    else:
        for task_id, task_def in tasks.items():
            if not isinstance(task_def, dict):
                errors.append(f"tasks.{task_id} must be a dictionary")
                continue

            # Validate description
            if "description" not in task_def:
                errors.append(f"tasks.{task_id} must have a 'description' field")
            elif not isinstance(task_def["description"], str):
                errors.append(f"tasks.{task_id}.description must be a string")

            # Validate expects format - CANONICAL FORMAT ONLY
            expects = task_def.get("expects", [])
            if not isinstance(expects, list):
                errors.append(f"tasks.{task_id}.expects must be a list")
            else:
                if not expects:
                    # Empty expects list is OK (no extraction needed)
                    pass
                else:
                    # All expects must be dict objects with "key" field
                    for k, exp in enumerate(expects):
                        if not isinstance(exp, dict):
                            errors.append(f"tasks.{task_id}.expects[{k}] must be a dict object, not a string. Use {{'key': '{exp}'}} instead of '{exp}'")
                        elif "key" not in exp:
                            errors.append(f"tasks.{task_id}.expects[{k}] missing required 'key' field")
                        elif not isinstance(exp["key"], str):
                            errors.append(f"tasks.{task_id}.expects[{k}].key must be a string")
                        else:
                            # Validate type if present
                            exp_type = exp.get("type", "string")
                            if exp_type not in ["string", "number", "enum"]:
                                errors.append(f"tasks.{task_id}.expects[{k}].type must be 'string', 'number', or 'enum'")

                            if exp_type == "number":
                                if "min" in exp and not isinstance(exp["min"], (int, float)):
                                    errors.append(f"tasks.{task_id}.expects[{k}].min must be a number")
                                if "max" in exp and not isinstance(exp["max"], (int, float)):
                                    errors.append(f"tasks.{task_id}.expects[{k}].max must be a number")
                            elif exp_type == "enum":
                                if "choices" not in exp:
                                    errors.append(f"tasks.{task_id}.expects[{k}] with type 'enum' must have 'choices' field")
                                elif not isinstance(exp["choices"], list):
                                    errors.append(f"tasks.{task_id}.expects[{k}].choices must be a list")
                                else:
                                    for choice in exp["choices"]:
                                        if not isinstance(choice, str):
                                            errors.append(f"tasks.{task_id}.expects[{k}].choices must contain only strings")

            # Validate silent flag
            if "silent" in task_def and not isinstance(task_def["silent"], bool):
                errors.append(f"tasks.{task_id}.silent must be a boolean")

    # Validate tones
    tones = data.get("tones", {})
    if not isinstance(tones, dict):
        errors.append("tones must be a dictionary")
    else:
        for tone_id, tone_def in tones.items():
            if isinstance(tone_def, dict):
                if "description" not in tone_def:
                    errors.append(f"tones.{tone_id} must have a 'description' field")
                elif not isinstance(tone_def["description"], str):
                    errors.append(f"tones.{tone_id}.description must be a string")
            elif not isinstance(tone_def, str):
                errors.append(f"tones.{tone_id} must be a string or object with description")

    # Validate tone reference
    tone_refs = data.get("tone", [])
    if not isinstance(tone_refs, list):
        errors.append("tone must be a list of tone IDs")
    else:
        for tone_ref in tone_refs:
            if not isinstance(tone_ref, str):
                errors.append("tone list must contain only strings")
            elif tone_ref not in tones:
                errors.append(f"tone '{tone_ref}' not defined in tones section")

    # Check for referenced but undefined tasks
    defined_tasks = set(tasks.keys())
    for block in plan:
        if isinstance(block, list):
            for task_id in block:
                if isinstance(task_id, str) and task_id not in defined_tasks:
                    errors.append(f"plan references undefined task '{task_id}'")

    return errors


def normalize_expects(expects: List[dict]) -> List[ExpectDefinition]:
    """Normalize expects format to ExpectDefinition objects (canonical format only)."""
    normalized = []
    for exp in expects:
        # All expects should be dict objects at this point (validated)
        normalized.append(ExpectDefinition(**exp))
    return normalized
