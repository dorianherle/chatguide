"""
Integration test showing how to use the complete extraction pipeline.
This demonstrates the full flow from config -> prompt -> LLM -> structured response.
"""

from yaml_reader import read_yaml_to_dict
from prompt import get_prompt_sidecar_director
from llm import talk_to_gemini_structured
from schema import ExtractionResponse
import os

def run_integration_test():
    """Complete integration test with real LLM call (requires API key)"""

    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("WARNING: No GEMINI_API_KEY environment variable found.")
        print("   Set your API key with: $env:GEMINI_API_KEY='your_key_here'")
        print("\nRunning in demo mode with mock response instead...\n")

        # Demo mode - show what would happen
        config_dict = read_yaml_to_dict('chatbot_config.yaml')
        conversation = "User: Hi, I'm John and I'm 30 years old from Boston."
        current_block = config_dict['blocks'][0]['fields']

        prompt = get_prompt_sidecar_director(conversation, current_block, [])
        print("Generated Prompt:")
        print("-" * 40)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

        # Mock response
        mock_response = ExtractionResponse(
            extracted={"name": "John", "age": "30", "origin": "Boston"},
            stage_direction="Ask about preferences next."
        )

        print("\nMock Structured Response:")
        print("-" * 40)
        print(f"Extracted: {mock_response.extracted}")
        print(f"Stage Direction: {mock_response.stage_direction}")

        return

    # Real integration test
    try:
        print("Running integration test with Gemini...")

        # Load config and create simple test scenario
        config_dict = read_yaml_to_dict('chatbot_config.yaml')

        # Simple conversation for testing
        conversation = """
User: Hello!
Assistant: Hi there! What's your name?
User: I'm Alex.
Assistant: Nice to meet you Alex! How old are you?
User: I'm 25.
Assistant: Great! Where are you from?
User: I'm from Seattle.
"""

        current_block = config_dict['blocks'][0]['fields']  # personal_info
        next_block = config_dict['blocks'][1]['fields']     # preferences

        # Generate prompt
        prompt = get_prompt_sidecar_director(conversation, current_block, next_block)

        # Call LLM with structured output
        response = talk_to_gemini_structured(prompt, api_key)

        print("SUCCESS: LLM Response received and validated!")
        print(f"\nExtracted values: {response.extracted}")
        print(f"Stage direction: {response.stage_direction}")

        # Verify structure
        assert isinstance(response.extracted, dict), "Extracted should be a dict"
        assert isinstance(response.stage_direction, str), "Stage direction should be a string"

        print("\nIntegration test passed!")

    except Exception as e:
        print(f"Integration test failed: {e}")
        print("Make sure your GEMINI_API_KEY is set correctly.")

if __name__ == "__main__":
    run_integration_test()
