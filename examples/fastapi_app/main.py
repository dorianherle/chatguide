"""
ChatGuide FastAPI App - Minimal serverless-like API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
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

# In-memory session storage (use Redis/database for production)
chat_sessions: Dict[str, Dict[str, Any]] = {}

class ChatRequest(BaseModel):
    message: Optional[str] = None
    session_id: Optional[str] = None
    action: str = "chat"  # "chat", "reset", "init"

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    progress: Dict[str, Any]
    finished: bool
    task_results: Optional[Dict[str, Any]] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - similar to Netlify function"""

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

        session_id = request.session_id or str(uuid.uuid4())

        # Get or create session
        session_data = chat_sessions.get(session_id)

        if request.action == "reset" or session_data is None:
            # Initialize new ChatGuide
            cg = ChatGuide(
                api_key=api_key,
                config="configs/config.yaml"
            )

            # Get initial response
            reply = cg.chat()

            # Store session
            chat_sessions[session_id] = {
                "chatguide": cg.dump(),
                "session_id": session_id
            }

            return ChatResponse(
                reply=reply.assistant_reply,
                session_id=session_id,
                progress=cg.get_progress(),
                finished=cg.is_finished(),
                task_results=getattr(reply, 'task_results', None)
            )

        # Restore ChatGuide from session
        cg = ChatGuide(
            api_key=api_key,
            config="configs/config.yaml"
        )
        cg.restore_from_dump(session_data["chatguide"])

        if request.action == "init":
            reply = cg.chat()
        elif request.message:
            cg.add_user_message(request.message)
            reply = cg.chat()
        else:
            raise HTTPException(status_code=400, detail="Message required for chat action")

        # Update session
        chat_sessions[session_id] = {
            "chatguide": cg.dump(),
            "session_id": session_id
        }

        return ChatResponse(
            reply=reply.assistant_reply,
            session_id=session_id,
            progress=cg.get_progress(),
            finished=cg.is_finished(),
            task_results=getattr(reply, 'task_results', None)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ChatGuide API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
