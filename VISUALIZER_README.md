# 🤖 Gearbox Chatbot Visualizer

A visual testing interface for the Gearbox chatbot system, built with Streamlit.

## Features

### Main Chat Window
- Clean conversation interface
- Real-time chat with the AI
- Message history display

### Engine Room Sidebar
- **Progress Bar**: Shows "Turn X of 5" until next audit cycle
- **Live State**: JSON view of extracted data (only updates after audits)
- **Director's Log**: Real-time console showing the Sidecar Director's thoughts
- **Current Block Info**: Shows current goal and missing fields

## Architecture

The visualizer demonstrates the **Director-Actor Pattern**:

1. **StateManager**: Tracks conversation progress and extracted data
2. **SidecarDirector**: Analyzes every 5th turn, extracts data, provides stage directions
3. **MainActor**: Generates natural, conversational responses based on director's guidance

## Running the Visualizer

```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Run the visualizer
streamlit run chatbot_visualizer.py
```

The app will open in your browser at `http://localhost:8501`

## How It Works

1. **Normal Conversation**: For the first 4 turns, the Actor responds naturally
2. **Audit Trigger**: On turn 5, the Director analyzes the conversation
3. **Data Extraction**: Director extracts any new information from user input
4. **State Update**: Live State JSON updates with new extracted data
5. **Block Progression**: When a block is complete, moves to the next goal
6. **Director Logging**: Shows the Director's analysis and decisions

## Configuration

- Edit `data_schema.yaml` to change conversation blocks and fields
- Modify turn threshold in the `StateManager` class (default: 5 turns)
- Adjust AI model settings in the Director/Actor classes

## Files

- `chatbot_visualizer.py` - Main Streamlit application
- `data_schema.yaml` - Conversation structure and goals
- `chatbot.py` - Original CLI version
- `requirements.txt` - Python dependencies

## Debug Features

- Full prompt visibility in the original CLI version (`python chatbot.py`)
- Director's log shows internal decision-making
- Live state updates demonstrate data extraction progress
- Progress bar visualizes the audit cycle timing

