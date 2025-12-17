#!/usr/bin/env python3
"""
Minimal example of using Gemini LLM with structured output
"""

from llm import talk_to_gemini, talk_to_gemini_structured
from schema import SimpleResponse

def main():
    # Example 1: Simple text response
    print("=== Example 1: Simple Text Response ===")
    prompt = "Explain what machine learning is in one sentence."
    response = talk_to_gemini(prompt)
    print(f"Response: {response}\n")

    # Example 2: Structured response
    print("=== Example 2: Structured Response ===")
    structured_prompt = """
    Analyze the following text: "I love programming with Python!"

    Return a structured analysis with:
    - A message summarizing the sentiment
    - Confidence score (0-1)
    - Category (positive/negative/neutral)
    """

    structured_response = talk_to_gemini_structured(structured_prompt)
    print(f"Message: {structured_response.message}")
    print(f"Confidence: {structured_response.confidence}")
    print(f"Category: {structured_response.category}")

if __name__ == "__main__":
    main()
