from pydantic import BaseModel, Field
from typing import Dict, Any

class ExtractionResponse(BaseModel):
    """
    Schema for the sidecar director's response containing extracted values and stage direction.
    """
    extracted: Dict[str, Any] = Field(description="Dictionary mapping field names to their extracted values")
    missing: Dict[str, Any] = Field(description="Dictionary mapping field names to their missing values")

class ConversationResponse(BaseModel):
    """
    Schema for the conversation LLM's response containing the bot's reply and completion status.
    """
    got_all_information: bool = Field(description="Whether all required information has been collected")
    response: str = Field(description="The bot's response to the user")