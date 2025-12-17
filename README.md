# Minimal Gemini LLM Example

This is a minimal example showing how to use Google's Gemini LLM with structured output in Python.

## Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up Environment Variables
1. Copy `env_example.txt` to `.env`
2. Add your Gemini API key to the `.env` file:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 5. Run the Example
```bash
python example.py
```

## Files Overview

- `requirements.txt` - Python dependencies
- `env_example.txt` - Environment variable template
- `schema.py` - Pydantic models for structured output
- `llm.py` - Gemini LLM integration functions
- `example.py` - Usage examples

## API Key

Get your Gemini API key from: https://aistudio.google.com/app/apikey

## Structured Output

The `talk_to_gemini_structured()` function uses Pydantic models to ensure the LLM returns properly structured JSON responses. This is useful for:
- Data extraction
- Classification tasks
- Structured information retrieval
- API responses