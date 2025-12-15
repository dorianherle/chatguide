# ChatGuide FastAPI App

Minimal FastAPI server for ChatGuide, similar to the Netlify serverless function but as a traditional web server.

## Features

- 🚀 **FastAPI**: Modern, fast Python web framework
- 💾 **Session Management**: In-memory session storage
- 🔄 **CORS Support**: Ready for web clients
- 📊 **Progress Tracking**: Real-time conversation progress
- 🏥 **Psychology-Ready**: Minimal, secure API design

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variable:**
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

3. **Run the server:**
   ```bash
   python main.py
   ```

4. **Open:** http://localhost:8000/static/index.html

## API Endpoints

### POST `/api/chat`
Chat with the AI assistant.

**Request:**
```json
{
  "message": "Hello!",
  "session_id": "optional-session-id",
  "action": "chat"
}
```

**Response:**
```json
{
  "reply": "Hi there! How can I help you today?",
  "session_id": "abc-123",
  "progress": {
    "completed": 1,
    "total": 5,
    "percent": 20
  },
  "finished": false
}
```

### GET `/health`
Health check endpoint.

## Actions

- `"chat"`: Send a message (requires `message`)
- `"reset"`: Start new conversation
- `"init"`: Initialize without sending message

## Deployment

### Railway (Recommended)
1. Connect your GitHub repo
2. Set `GEMINI_API_KEY` in environment variables
3. Deploy!

### Render
1. Create new Web Service
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Local Development
```bash
uvicorn main:app --reload
```

## Security Notes

- Configure CORS properly for production
- Use proper session storage (Redis/PostgreSQL) for production
- Add authentication middleware for psychology app
- Enable HTTPS in production


