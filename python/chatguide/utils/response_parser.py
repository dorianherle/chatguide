"""Response parser - parses LLM responses."""

import json
from typing import Any, List
from ..schemas import ChatGuideReply, TaskResult


def parse_llm_response(raw: Any) -> ChatGuideReply:
    """Parse LLM response into ChatGuideReply."""
    if raw is None:
        raise ValueError("LLM returned no content")

    if isinstance(raw, ChatGuideReply):
        return raw
    
    if isinstance(raw, dict):
        # Handle task_id field from LLM responses (prompt asks for it but schema doesn't have it)
        # Also deduplicate by key to prevent duplicate extractions
        if "task_results" in raw and isinstance(raw["task_results"], list):
            processed_results = []
            seen_keys = set()
            for tr in raw["task_results"]:
                if isinstance(tr, dict):
                    key = tr.get("key", "")
                    # Skip duplicates
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        processed_results.append({
                            "key": key,
                            "value": tr.get("value", "")
                        })
                else:
                    processed_results.append(tr)
            raw["task_results"] = processed_results
        return ChatGuideReply.model_validate(raw)
    
    if isinstance(raw, str):
        parsed = json.loads(raw)
        # Handle task_id field from LLM responses and deduplicate
        if "task_results" in parsed and isinstance(parsed["task_results"], list):
            processed_results = []
            seen_keys = set()
            for tr in parsed["task_results"]:
                if isinstance(tr, dict):
                    key = tr.get("key", "")
                    # Skip duplicates
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        processed_results.append({
                            "key": key,
                            "value": tr.get("value", "")
                        })
                else:
                    processed_results.append(tr)
            parsed["task_results"] = processed_results
        return ChatGuideReply.model_validate(parsed)
    
    raise ValueError(f"Unexpected response type: {type(raw)}")
