from yaml_reader import read_yaml_to_dict
from prompt import get_prompt_sidecar_director
from schema import ExtractionResponse
import json

def test_extraction_flow():
    """Test the complete extraction flow with mock data"""

    # Load configuration
    config_dict = read_yaml_to_dict('chatbot_config.yaml')

    # Mock conversation with some user responses
    mock_conversation = """
User: Hi there!
Assistant: Hello! I'd love to get to know you better. What's your name?
User: My name is Sarah.
Assistant: Nice to meet you Sarah! How old are you?
User: I'm 28 years old.
Assistant: Great! Where are you from originally?
User: I'm from Toronto, Canada.
"""

    # Get current and next extraction blocks
    current_block = config_dict['blocks'][0]['fields']  # personal_info
    next_block = config_dict['blocks'][1]['fields']     # preferences

    # Generate the prompt
    prompt = get_prompt_sidecar_director(mock_conversation, current_block, next_block)

    print("=== GENERATED PROMPT ===")
    print(prompt)
    print("\n" + "="*50 + "\n")

    # Mock LLM response (what Gemini would return)
    mock_llm_response = {
        "extracted": {
            "name": "Sarah",
            "age": "28",
            "origin": "Toronto, Canada"
        },
        "stage_direction": "The user has provided their name, age, and origin. Now transition to asking about their preferences by asking about their favorite color to start the preferences block."
    }

    print("=== MOCK LLM RESPONSE ===")
    print(json.dumps(mock_llm_response, indent=2))

    # Validate against schema
    try:
        validated_response = ExtractionResponse(**mock_llm_response)
        print("\n[SUCCESS] Response validates against schema!")

        # Show how to access the data
        print(f"\nExtracted fields: {list(validated_response.extracted.keys())}")
        print(f"Number of fields extracted: {len(validated_response.extracted)}")
        print(f"Stage direction: {validated_response.stage_direction[:100]}...")

        # Demonstrate accessing individual fields
        print("\nIndividual extracted values:")
        for field_name, value in validated_response.extracted.items():
            print(f"  {field_name}: {value}")

    except Exception as e:
        print(f"\nX Schema validation failed: {e}")

    print("\n" + "="*50)
    print("JSON Schema sent to Gemini:")
    print(json.dumps(ExtractionResponse.model_json_schema(), indent=2))

if __name__ == "__main__":
    test_extraction_flow()
