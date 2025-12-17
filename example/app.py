from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import asyncio
import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yaml_reader import read_yaml_to_dict
from prompt import get_prompt_conversation_llm, get_prompt_sidecar_director
from llm import talk_to_gemini, talk_to_gemini_structured

# Load .env from the current directory (example folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please make sure the .env file exists in the example directory with your Gemini API key.")

app = FastAPI(title="ChatGuide Frontend")

# Get the directory containing this script
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "frontend", "static")
templates_dir = os.path.join(current_dir, "frontend", "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Global state
config_dict = read_yaml_to_dict(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chatbot_config.yaml'))
active_connections = []
conversation_data = {
    "conversation": "",
    "turn_count": 0,
    "current_director_response": None,
    "extracted_data": {}
}

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # Initialize conversation if first connection
        if conversation_data["conversation"] == "":
            await initialize_conversation()

        # Send initial state
        await websocket.send_json({
            "type": "initial_state",
            "conversation": conversation_data["conversation"],
            "turn_count": conversation_data["turn_count"],
            "director_data": conversation_data["current_director_response"].model_dump() if conversation_data["current_director_response"] else None
        })

        while True:
            data = await websocket.receive_json()

            if data["type"] == "user_message":
                user_input = data["message"]
                await handle_user_message(websocket, user_input)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

async def initialize_conversation():
    """Initialize the conversation with the first director prompt"""
    to_extract = config_dict['blocks'][0]['fields']
    next_extraction_block = config_dict['blocks'][1]['fields']

    initial_sidecar_prompt = get_prompt_sidecar_director("", to_extract, next_extraction_block)
    response = talk_to_gemini_structured(initial_sidecar_prompt, api_key=GEMINI_API_KEY)
    conversation_data["current_director_response"] = response

    # Generate initial bot response
    persona = "You are a friendly and engaging chatbot. Keep sentences very short and concise."
    conversation_prompt = get_prompt_conversation_llm(persona, "", response.stage_direction)

    bot_response = talk_to_gemini(conversation_prompt, api_key=GEMINI_API_KEY)
    conversation_data["conversation"] = f"You: {bot_response}\n"

async def handle_user_message(websocket: WebSocket, user_input: str):
    """Handle a user message and generate bot response"""
    global conversation_data

    # Add user message to conversation
    conversation_data["conversation"] += f"User: {user_input}\n"
    conversation_data["turn_count"] += 1

    # Notify all clients about audit state if needed
    should_audit = conversation_data["turn_count"] % 3 == 0

    if should_audit:
        # Send audit start notification
        await broadcast({
            "type": "audit_start"
        })

        # Update director
        to_extract = config_dict['blocks'][0]['fields']
        next_extraction_block = config_dict['blocks'][1]['fields']

        sidecar_prompt = get_prompt_sidecar_director(conversation_data["conversation"], to_extract, next_extraction_block)
        director_response = talk_to_gemini_structured(sidecar_prompt, api_key=GEMINI_API_KEY)
        conversation_data["current_director_response"] = director_response

        await broadcast({
            "type": "director_update",
            "data": director_response.model_dump()
        })

    # Generate bot response
    persona = "You are a friendly and engaging chatbot. Keep sentences very short and concise."
    stage_direction = conversation_data["current_director_response"].stage_direction if conversation_data["current_director_response"] else ""
    conversation_prompt = get_prompt_conversation_llm(persona, conversation_data["conversation"], stage_direction)

    bot_response = talk_to_gemini(conversation_prompt, api_key=GEMINI_API_KEY)
    conversation_data["conversation"] += f"You: {bot_response}\n"

    # Send bot response
    await websocket.send_json({
        "type": "bot_message",
        "message": bot_response,
        "turn_count": conversation_data["turn_count"]
    })

    if should_audit:
        await broadcast({
            "type": "audit_end"
        })

async def broadcast(message):
    """Broadcast message to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            # Remove dead connections
            if connection in active_connections:
                active_connections.remove(connection)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
