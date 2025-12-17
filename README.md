# Conversational Chatbot System

A state-based conversational AI system that extracts structured data while maintaining engaging conversations. Uses Google's Gemini API with a main conversation LLM and a monitoring sidecar LLM.

## Features

- **State-based conversations**: Tracks extracted data and conversation progress
- **Block-based data extraction**: Organized data collection in logical blocks
- **Dual LLM architecture**: Main chatbot + sidecar monitor for intelligent prompt adjustment
- **Dynamic prompt adaptation**: Sidecar LLM analyzes progress and refocuses conversation as needed
- **Interactive testing**: See how data extraction, prompt changes, and block transitions work

## Files

- `conversational_chatbot.py` - Main chatbot implementation
- `chatbot_config.yaml` - Configuration for data blocks and prompts
- `test_chatbot.py` - Interactive test interface
- `gemini_sample.py` - Basic Gemini API example

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set your Gemini API key in `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### Interactive Testing
```bash
python test_chatbot.py
```
Choose from:
1. Interactive conversation test
2. Data extraction demo
3. Both tests

### Direct Usage
```python
from conversational_chatbot import ConversationalChatbot

chatbot = ConversationalChatbot()
response = chatbot.process_user_message("Hi, I'm Alex!")
print(response)
```

### Commands in Interactive Mode
- `status` - Show current extraction progress
- `reset` - Start fresh conversation
- `quit` - Exit

## How It Works

1. **Data Blocks**: Configured in `chatbot_config.yaml` with fields to extract
2. **State Tracking**: Monitors what's been extracted and what's missing
3. **Main LLM**: Handles engaging conversation with current prompt
4. **Sidecar LLM**: Monitors every N turns and adjusts main LLM prompt
5. **Block Transitions**: Moves to next data block when requirements met

## Gemini Sample

See `gemini_sample.py` for a minimal example of how to talk to Google's Gemini AI.

## Old Code

Your previous code is preserved in the `main` branch. You can access it anytime with:
```bash
git checkout main
```