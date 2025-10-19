"""Test silent tasks functionality."""

import os
from dotenv import load_dotenv
from src.chatguide import ChatGuide

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")

if not api_key:
    print("ERROR: No API key")
    exit(1)

print("="*60)
print("TESTING SILENT TASKS")
print("="*60)

cg = ChatGuide(api_key=api_key, debug=False)
cg.load_config("realistic_hotel_config.yaml")

print("\n[1] Initial greeting...")
reply = cg.chat()
print(f"Assistant: {reply.assistant_reply}")

print("\n[2] User selects Check In...")
cg.state.set("purpose", "Check In")
cg.add_user_message("Check In")
cg.adjustments.evaluate(cg.state, cg.plan, cg.tone)
print(f"Plan jumped to: {cg.plan.get_current_block()}")

print("\n[3] User provides name (silent task + greeting with tone)...")
print("User: My name is Sarah Johnson")
cg.add_user_message("My name is Sarah Johnson")

# This should:
# - Call LLM #1: Extract name (silent, no reply shown)
# - Fire adjustment: recognize_returning → tone changes
# - Call LLM #2: Greet with new tone (returning_guest)
reply = cg.chat()

print(f"\n[RESULT]")
print(f"Assistant: {reply.assistant_reply}")
print(f"State: {cg.state.to_dict()}")
print(f"Tone: {cg.tone}")
print(f"Adjustments fired: {cg.get_last_fired_adjustments()}")
print(f"History length: {len(cg.conversation_history)}")

# Check if the greeting uses returning guest tone
if "!" in reply.assistant_reply and "back" in reply.assistant_reply.lower():
    print("\n[SUCCESS] Returning guest tone detected in first response!")
else:
    print("\n[PARTIAL] Response may not have returning guest excitement")

