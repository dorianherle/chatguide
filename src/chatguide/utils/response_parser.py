"""Response parser - parses LLM responses."""

import json
from typing import Any
from ..schemas import ChatGuideReply


def parse_llm_response(raw: Any) -> ChatGuideReply:
    """Parse LLM response into ChatGuideReply."""
    if raw is None:
        raise ValueError("LLM returned no content")

    if isinstance(raw, ChatGuideReply):
        return raw
    
    if isinstance(raw, dict):
        return ChatGuideReply.model_validate(raw)
    
    if isinstance(raw, str):
        return ChatGuideReply.model_validate(json.loads(raw))
    
    raise ValueError(f"Unexpected response type: {type(raw)}")
