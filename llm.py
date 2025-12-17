from google import genai
from schema import ExtractionResponse

def talk_to_gemini(prompt: str, api_key: str = None) -> str:
    """Send a prompt to Gemini and get a response"""

    # Create Gemini client
    client = genai.Client(api_key=api_key)


    # Send prompt and get response
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )

    # Return the text response
    return response.text

def talk_to_gemini_structured(prompt: str, api_key: str = None) -> ExtractionResponse:
    """Send a prompt to Gemini and get a structured response"""
    import json
  

    # Create Gemini client
    client = genai.Client(api_key=api_key)

    # Configure the model
    config = {
        "response_mime_type": "application/json",
        "response_json_schema": ExtractionResponse.model_json_schema(),
    }

    # Send prompt and get response
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=config,
    )

    # Parse and validate the JSON response
    response_data = json.loads(response.text)
    return ExtractionResponse(**response_data)