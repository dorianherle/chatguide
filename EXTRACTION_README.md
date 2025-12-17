# Chatbot Extraction System

This system implements structured data extraction from conversations using JSON schemas and Pydantic validation.

## Overview

The system consists of:
- **YAML Configuration**: Define extraction blocks and fields in `chatbot_config.yaml`
- **Prompt Generation**: Format prompts for LLM using `prompt.py`
- **Schema Validation**: Pydantic models ensure structured responses in `schema.py`
- **LLM Integration**: Gemini API calls with JSON schema enforcement in `llm.py`

## Key Components

### 1. Configuration (`chatbot_config.yaml`)
```yaml
blocks:
  - name: "personal_info"
    description: "Extract basic personal information"
    turns_threshold: 3
    fields:
      - name: "name"
        question: "What is your name?"
      - name: "age"
        question: "How old are you?"
        validation: "is_integer and 0 < value < 90"
```

### 2. Expected JSON Response Format
```json
{
  "extracted": {
    "name": "John Doe",
    "age": "25",
    "origin": "New York"
  },
  "stage_direction": "Instructions for conversation LLM to continue the dialogue."
}
```

### 3. Pydantic Schema (`schema.py`)
```python
class ExtractionResponse(BaseModel):
    extracted: Dict[str, Any] = Field(description="Dictionary mapping field names to their extracted values")
    stage_direction: str = Field(description="Instructions for the conversation LLM")
```

## Usage Examples

### Basic Extraction Test
```python
from yaml_reader import read_yaml_to_dict
from prompt import get_prompt_sidecar_director
from llm import talk_to_gemini_structured

# Load config
config = read_yaml_to_dict('chatbot_config.yaml')

# Generate prompt
conversation = "User: Hi, I'm Sarah from Toronto, 28 years old."
current_fields = config['blocks'][0]['fields']
next_fields = config['blocks'][1]['fields']

prompt = get_prompt_sidecar_director(conversation, current_fields, next_fields)

# Get structured response
response = talk_to_gemini_structured(prompt, api_key)
print(response.extracted)  # {'name': 'Sarah', 'age': '28', 'origin': 'Toronto'}
print(response.stage_direction)  # Instructions for next conversation step
```

### Running Tests
```bash
# Test schema validation
python test_schema.py

# Test complete extraction flow
python test_extraction.py

# Integration test (requires API key)
python integration_test.py
```

## API Key Setup

Set your Gemini API key:
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

## Benefits

1. **Structured Output**: Gemini returns validated JSON matching your schema
2. **Type Safety**: Pydantic validates response structure at runtime
3. **Clear Interface**: Well-defined contracts between components
4. **Easy Testing**: Mock responses validate against the same schema
5. **Documentation**: Schema serves as living documentation

## File Structure
```
├── chatbot_config.yaml    # Extraction configuration
├── schema.py             # Pydantic models
├── prompt.py             # Prompt generation
├── llm.py                # Gemini integration
├── yaml_reader.py        # Config loading
├── test_*.py             # Test files
└── main.py               # Example usage
```

