from pydantic import BaseModel, Field

class SimpleResponse(BaseModel):
    """
    Simple schema for structured LLM responses
    """
    message: str = Field(description="The response message")
    confidence: float = Field(description="Confidence score between 0-1")
    category: str = Field(description="Category of the response")