"""Configuration file loader and parser."""

import json
from typing import Dict, Any, Tuple, List


def load_config_file(path: str) -> dict:
    """Load configuration from YAML or JSON file."""
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        if path.endswith((".yml", ".yaml")):
            return yaml.safe_load(f)
        return json.load(f)


def parse_guardrails(data: dict) -> str:
    """Extract and format guardrails from config."""
    if "guardrails" not in data:
        return ""
    
    guardrails = data["guardrails"]
    if isinstance(guardrails, dict):
        return "\n".join([f"• {k.title()}: {v}" for k, v in guardrails.items()])
    return guardrails


def parse_tasks(data: dict) -> Dict[str, str]:
    """Extract tasks from config."""
    return data.get("tasks", {})


def parse_tones(data: dict) -> Dict[str, str]:
    """Extract tones from config."""
    return data.get("tones", {})


def parse_routes(data: dict) -> List[Dict[str, Any]]:
    """Extract routes from config."""
    return data.get("routes", [])

