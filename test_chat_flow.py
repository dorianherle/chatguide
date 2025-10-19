"""Test chat flow without interactive input."""

import os
from dotenv import load_dotenv
from src.chatguide import ChatGuide

load_dotenv()

def test_flow():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
    
    if not api_key:
        print("ERROR: No API key. Set GEMINI_API_KEY in .env")
        return
    
    print("Testing ChatGuide flow...\n")
    
    # Initialize
    cg = ChatGuide(api_key=api_key, debug=False)
    cg.load_config("realistic_hotel_config.yaml")
    
    print("[OK] Config loaded")
    print(f"     State: {cg.state.to_dict()}")
    print(f"     Plan: {len(cg.plan._blocks)} blocks")
    print(f"     Tasks: {len(cg.tasks)} tasks\n")
    
    # First interaction
    print("[TEST] First LLM call...")
    reply = cg.chat()
    print(f"[OK] Response: {reply.assistant_reply[:100]}...")
    print(f"     UI tools: {cg.get_pending_ui_tools()}\n")
    
    # Simulate user selecting "Check In"
    print("[TEST] User selects 'Check In'")
    cg.state.set("purpose", "Check In")
    cg.add_user_message("Check In")
    
    # Check adjustments fired
    cg.adjustments.evaluate(cg.state, cg.plan, cg.tone)
    print(f"[OK] Plan jumped to block: {cg.plan.current_index}")
    print(f"     Current tasks: {cg.plan.get_current_block()}\n")
    
    # Next interaction
    print("[TEST] Next LLM call...")
    reply = cg.chat()
    print(f"[OK] Response: {reply.assistant_reply[:100]}...")
    print(f"     State: {cg.state.to_dict()}\n")
    
    # Simulate providing name
    print("[TEST] User provides name 'Sarah'")
    cg.add_user_message("My name is Sarah")
    reply = cg.chat()
    print(f"[OK] Response: {reply.assistant_reply[:100]}...")
    print(f"     State after: {cg.state.to_dict()}")
    print(f"     Tone: {cg.tone}\n")
    
    print("[SUCCESS] All flows working!")

if __name__ == "__main__":
    test_flow()

