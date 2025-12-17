from schema import ExtractionResponse
import json

# Example of what the LLM would return
example_response = {
    "extracted": {
        "name": "John Doe",
        "age": "25",
        "origin": "New York"
    },
    "stage_direction": "Ask about their favorite color to transition to preferences."
}

# Validate it against our schema
try:
    validated_response = ExtractionResponse(**example_response)
    print("Valid response!")
    print(f"Extracted: {validated_response.extracted}")
    print(f"Stage direction: {validated_response.stage_direction}")

    # Access individual extracted fields
    print(f"\nName: {validated_response.extracted.get('name')}")
    print(f"Age: {validated_response.extracted.get('age')}")

except Exception as e:
    print(f"Invalid response: {e}")

# Show the JSON schema that gets sent to Gemini
print("\n=== JSON SCHEMA SENT TO GEMINI ===")
print(json.dumps(ExtractionResponse.model_json_schema(), indent=2))
