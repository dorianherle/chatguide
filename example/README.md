# ChatGuide Frontend Example

A FastAPI-based web frontend for the ChatGuide chatbot system with a sci-fi administrative console theme.

## Features

- **Split-Screen Dashboard**: Chat interface on the left, Director control panel on the right
- **Dark Mode Theme**: Slate-900 color scheme with sci-fi aesthetic
- **Real-time Communication**: WebSocket-based chat with live updates
- **Director Integration**: Visual representation of the chatbot's internal director system
- **Responsive Design**: Sidebar hidden on mobile devices
- **Turn Inspector**: Click on bot messages to see internal state and directives

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have your `.env` file in the parent directory with your `GEMINI_API_KEY`

3. Run the application:
```bash
python app.py
```

4. Open your browser to `http://localhost:8000`

## Architecture

- **Backend**: FastAPI with WebSocket support
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS
- **Real-time Updates**: WebSocket connection for live chat
- **State Management**: Global conversation state shared across all connected clients

## UI Components

### Chat Interface (Left Panel)
- Message bubbles with different alignments for user/bot
- Typing indicators during bot response generation
- Audit overlay during director analysis
- Input bar with send button

### Director Panel (Right Sidebar)
- **Status Pill**: Shows MONITORING or AUDITING state
- **Epoch Progress**: Visual progress bar for turn cycles
- **Active Blueprint Block**: Current extraction targets and progress
- **Current Standing Order**: Active directive from the director
- **Extracted Knowledge**: JSON display of collected data
- **Director's Log**: History of director actions

### Turn Inspector Modal
- Static Persona: The chatbot's core personality
- Active Mandate: Current director directive
- Resulting Message: The actual bot response

## WebSocket Events

- `initial_state`: Initial conversation and director state
- `bot_message`: New bot response with turn count
- `audit_start`: Director analysis beginning
- `audit_end`: Director analysis complete
- `director_update`: Director state changes
