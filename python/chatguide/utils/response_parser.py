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
        # Handle task_id field from LLM responses
        # Deduplicate by (task_id, key) pair to allow same key for different tasks
        if "task_results" in raw and isinstance(raw["task_results"], list):
            processed_results = []
            seen = set()
            for tr in raw["task_results"]:
                if isinstance(tr, dict):
                    task_id = tr.get("task_id", "")
                    key = tr.get("key", "")
                    pair = (task_id, key)
                    # Skip duplicates by (task_id, key) pair
                    if key and pair not in seen:
                        seen.add(pair)
                        processed_results.append({
                            "task_id": task_id,
                            "key": key,
                            "value": tr.get("value", "")
                        })
                else:
                    processed_results.append(tr)
            raw["task_results"] = processed_results
        return ChatGuideReply.model_validate(raw)
    
    if isinstance(raw, str):
        parsed = json.loads(raw)
        # Handle task_id field from LLM responses
        # Deduplicate by (task_id, key) pair to allow same key for different tasks
        if "task_results" in parsed and isinstance(parsed["task_results"], list):
            processed_results = []
            seen = set()
            for tr in parsed["task_results"]:
                if isinstance(tr, dict):
                    task_id = tr.get("task_id", "")
                    key = tr.get("key", "")
                    pair = (task_id, key)
                    # Skip duplicates by (task_id, key) pair
                    if key and pair not in seen:
                        seen.add(pair)
                        processed_results.append({
                            "task_id": task_id,
                            "key": key,
                            "value": tr.get("value", "")
                        })
                else:
                    processed_results.append(tr)
            parsed["task_results"] = processed_results
        return ChatGuideReply.model_validate(parsed)
    
    raise ValueError(f"Unexpected response type: {type(raw)}")
