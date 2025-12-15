"""
ChatGuide FastAPI App - Minimal serverless-like API
"""

import sys
from pathlib import Path

# Add the python directory to path (works from any directory)
script_dir = Path(__file__).parent
python_dir = script_dir.parent.parent / 'python'
sys.path.insert(0, str(python_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Import ChatGuide
from chatguide import ChatGuide

# Load environment variables
load_dotenv()

app = FastAPI(title="ChatGuide API", description="Conversational AI API")

# CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = Path(__file__).parent / "static"

# Project root and config path
PROJECT_ROOT = Path(__file__).parent.parent.parent  # chatguide/
CONFIG_PATH = str(PROJECT_ROOT / "configs" / "config.yaml")
LOG_FILE = PROJECT_ROOT / "debug_log.json"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Root redirect to static index
@app.get("/")
async def root():
    """Redirect to the chat interface"""
    return FileResponse(STATIC_DIR / "index.html")

# In-memory session storage (use Redis/database for production)
chat_sessions: Dict[str, ChatGuide] = {}

class ChatRequest(BaseModel):
    message: Optional[str] = None
    session_id: Optional[str] = None
    action: str = "chat"  # "chat", "reset", "init"

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    progress: Dict[str, Any]
    finished: bool
    task_results: Optional[Any] = None
    state_data: Optional[Dict[str, Any]] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - similar to Netlify function"""

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

        session_id = request.session_id or str(uuid.uuid4())

        # Get or create session
        cg = chat_sessions.get(session_id)

        if request.action == "reset" or cg is None:
            # Initialize new ChatGuide
            cg = ChatGuide(
                api_key=api_key,
                config=CONFIG_PATH,
                debug=True
            )

            # Get initial response
            reply = cg.chat()

            # Store session
            chat_sessions[session_id] = cg

            # Convert state to JSON-serializable dict
            state_dict = {
                "data": cg.state["data"],
                "messages": cg.state["messages"],
                "block": cg.state["block"],
                "completed": list(cg.state["completed"]),  # Convert set to list
                "recent_keys": cg.state["recent_keys"]
            }

            return ChatResponse(
                reply=reply.text,
                session_id=session_id,
                progress=cg.get_progress(),
                finished=cg.is_finished(),
                task_results=reply.task_results,
                state_data=state_dict
            )

        # Use existing session
        if request.action == "init":
            reply = cg.chat()
        elif request.message:
            cg.add_user_message(request.message)
            reply = cg.chat()
        else:
            raise HTTPException(status_code=400, detail="Message required for chat action")

        # Convert state to JSON-serializable dict
        state_dict = {
            "data": cg.state["data"],
            "messages": cg.state["messages"],
            "block": cg.state["block"],
            "completed": list(cg.state["completed"]),  # Convert set to list
            "recent_keys": cg.state["recent_keys"]
        }

        return ChatResponse(
            reply=reply.text,
            session_id=session_id,
            progress=cg.get_progress(),
            finished=cg.is_finished(),
            task_results=reply.task_results,
            state_data=state_dict
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ChatGuide API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))


