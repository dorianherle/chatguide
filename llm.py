from google import genai
from schema import SimpleResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_gemini_client(api_key=None):
    """Create and return Gemini client"""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=key)

def talk_to_gemini(prompt: str, api_key: str = None) -> str:
    """Send a prompt to Gemini and get a text response"""
    client = get_gemini_client(api_key)

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
    )

    return response.text

def talk_to_gemini_structured(prompt: str, api_key: str = None, response_schema=SimpleResponse) -> SimpleResponse:
    """Send a prompt to Gemini and get a structured response"""
    import json

    client = get_gemini_client(api_key)

    # Configure the model for JSON output
    config = {
        "response_mime_type": "application/json",
        "response_json_schema": response_schema.model_json_schema(),
    }

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt,
        config=config,
    )

    # Parse and validate the JSON response
    response_data = json.loads(response.text)
    return response_schema(**response_data)