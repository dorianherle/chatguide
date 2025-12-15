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
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY environment variable is not set. Please configure your Gemini API key."
            )
        if not api_key.startswith("AIza"):
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY appears to be invalid. Gemini API keys should start with 'AIza'."
            )

        session_id = request.session_id or str(uuid.uuid4())

        # Get or create session
        cg = chat_sessions.get(session_id)

        if request.action == "reset" or cg is None:
            # Initialize new ChatGuide
            try:
                cg = ChatGuide(
                    api_key=api_key,
                    config=CONFIG_PATH,
                    debug=True
                )
            except Exception as config_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Configuration error: {str(config_error)}"
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


@app.post("/api/reload-config")
async def reload_config():
    """Reload configuration for all active sessions"""
    try:
        reloaded_count = 0
        failed_count = 0

        for session_id, cg in chat_sessions.items():
            if cg.reload_config():
                reloaded_count += 1
            else:
                failed_count += 1

        return {
            "status": "config_reloaded",
            "reloaded_sessions": reloaded_count,
            "failed_sessions": failed_count,
            "total_sessions": len(chat_sessions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config reload error: {str(e)}")


@app.get("/api/progress/{session_id}")
async def get_progress(session_id: str):
    """Get detailed progress information for a session"""
    try:
        cg = chat_sessions.get(session_id)
        if not cg:
            raise HTTPException(status_code=404, detail="Session not found")

        progress = cg.get_progress()

        # Enhanced progress info
        current_block = cg.state["block"]
        total_blocks = len(cg.config["blocks"])

        block_progress = []
        for i in range(total_blocks):
            block_tasks = cg.config["blocks"][i] if i < len(cg.config["blocks"]) else []
            completed_in_block = sum(1 for tid in block_tasks if tid in cg.state["completed"])
            block_progress.append({
                "block_index": i,
                "total_tasks": len(block_tasks),
                "completed_tasks": completed_in_block,
                "is_current": i == current_block,
                "is_completed": i < current_block
            })

        return {
            "session_id": session_id,
            "finished": cg.is_finished(),
            "overall_progress": progress,
            "block_progress": block_progress,
            "current_block_details": {
                "index": current_block,
                "tasks": [
                    {
                        "id": tid,
                        "description": cg.config["tasks"].get(tid, {}).get("description", ""),
                        "completed": tid in cg.state["completed"]
                    } for tid in (cg.config["blocks"][current_block] if current_block < total_blocks else [])
                ]
            } if current_block < total_blocks else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Progress error: {str(e)}")


@app.get("/api/debug/{session_id}")
async def debug_session(session_id: str):
    """Debug endpoint to inspect session state"""
    try:
        cg = chat_sessions.get(session_id)
        if not cg:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get detailed state information
        current_block = cg.state["block"]
        total_blocks = len(cg.config["blocks"])

        # Get current block tasks
        current_block_tasks = []
        if current_block < total_blocks:
            for task_id in cg.config["blocks"][current_block]:
                task_def = cg.config["tasks"].get(task_id, {})
                current_block_tasks.append({
                    "id": task_id,
                    "description": task_def.get("description", ""),
                    "expects": [exp.key if hasattr(exp, 'key') else exp for exp in task_def.get("expects", [])],
                    "completed": task_id in cg.state["completed"],
                    "silent": task_def.get("silent", False)
                })

        # Get pending tasks across all blocks
        pending_tasks = []
        for block_idx, block in enumerate(cg.config["blocks"]):
            for task_id in block:
                if task_id not in cg.state["completed"]:
                    task_def = cg.config["tasks"].get(task_id, {})
                    pending_tasks.append({
                        "id": task_id,
                        "block": block_idx,
                        "description": task_def.get("description", ""),
                        "expects": [exp.key if hasattr(exp, 'key') else exp for exp in task_def.get("expects", [])]
                    })

        return {
            "session_id": session_id,
            "finished": cg.is_finished(),
            "current_block": current_block,
            "total_blocks": total_blocks,
            "progress": cg.get_progress(),
            "current_block_tasks": current_block_tasks,
            "pending_tasks": pending_tasks,
            "completed_tasks": list(cg.state["completed"]),
            "extracted_data": cg.state["data"],
            "recent_keys": cg.state["recent_keys"],
            "conversation_length": len(cg.state["messages"]),
            "config_summary": {
                "total_tasks": len(cg.config["tasks"]),
                "tone": cg.config["tone"],
                "language": cg.config["language"]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))


