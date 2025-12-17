from pydantic import BaseModel, Field
from typing import Dict, Any

class ExtractionResponse(BaseModel):
    """
    Schema for the sidecar director's response containing extracted values and stage direction.
    """
    extracted: Dict[str, Any] = Field(description="Dictionary mapping field names to their extracted values")
    stage_direction: str = Field(description="Instructions for the conversation LLM to steer the conversation forward")
