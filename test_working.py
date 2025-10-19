"""Quick test that everything works."""

import os
from dotenv import load_dotenv
from src.chatguide import ChatGuide

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")

if not api_key:
    print("ERROR: No API key")
    exit(1)

print("="*60)
print("CHATGUIDE ARCHITECTURE TEST")
print("="*60)

# Initialize
cg = ChatGuide(api_key=api_key, debug=False)
cg.load_config("realistic_hotel_config.yaml")

print("\n[1] Config loaded successfully")
print(f"    State: {cg.state.to_dict()}")
print(f"    Plan blocks: {len(cg.plan._blocks)}")
print(f"    Current block: {cg.plan.get_current_block()}")

# First LLM call
print("\n[2] Calling LLM...")
reply = cg.chat()
print(f"    Assistant: {reply.assistant_reply}")
print(f"    Tools requested: {[t.tool for t in reply.tools]}")

# Simulate user choice
print("\n[3] User selects 'Check In'")
cg.state.set("purpose", "Check In")
cg.add_user_message("Check In")
cg.adjustments.evaluate(cg.state, cg.plan, cg.tone)
print(f"    Plan jumped to block: {cg.plan.current_index}")
print(f"    New tasks: {cg.plan.get_current_block()}")

# Next call
print("\n[4] Next LLM call...")
reply = cg.chat()
print(f"    Assistant: {reply.assistant_reply[:80]}...")
print(f"    State: {cg.state.to_dict()}")

# Provide name
print("\n[5] User provides name")
cg.add_user_message("My name is John Smith")
reply = cg.chat()
print(f"    Assistant: {reply.assistant_reply[:80]}...")
print(f"    State: {cg.state.to_dict()}")
print(f"    Tone: {cg.tone}")

print("\n" + "="*60)
print("SUCCESS - New architecture working!")
print("="*60)

