#!/usr/bin/env python3
"""
Minimal Gemini API Sample
Shows how to talk to Google's Gemini AI
"""

import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def talk_to_gemini(prompt: str, api_key: str = None) -> str:
    """Send a prompt to Gemini and get a response"""

    # Use API key from parameter or environment
    api_key = api_key or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Set it in .env file or pass as parameter")

    # Create Gemini client
    client = genai.Client(api_key=api_key)

    # Configure the model
    config = {
        "temperature": 0.6,
        "max_output_tokens": 256,
    }

    # Send prompt and get response
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=config,
    )

    # Return the text response
    return response.text

if __name__ == "__main__":
    # Example usage
    prompt = "Hello! Can you tell me a short joke?"
    try:
        response = talk_to_gemini(prompt)
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
