"""Test the new ChatGuide architecture."""

import os
from dotenv import load_dotenv
from src.chatguide import ChatGuide

load_dotenv()

def test_basic_flow():
    """Test basic conversational flow."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
    
    if not api_key:
        print("WARNING: No API key found. Set GEMINI_API_KEY or GEMINI_API in .env file")
        return
    
    print("Testing new ChatGuide architecture...\n")
    
    # Initialize
    cg = ChatGuide(api_key=api_key, debug=True)
    cg.load_config("realistic_hotel_config.yaml")
    
    print("[OK] Config loaded")
    print(f"   State: {cg.state.to_dict()}")
    print(f"   Plan blocks: {len(cg.plan._blocks)}")
    print(f"   Tasks: {list(cg.tasks.keys())}")
    print(f"   Tone: {cg.tone}")
    print(f"   Adjustments: {len(cg.adjustments._adjustments)}\n")
    
    # Test first interaction
    print("[TEST] Getting first response...")
    try:
        reply = cg.chat()
        print(f"[OK] LLM responded")
        print(f"   Message: {reply.assistant_reply[:100]}...")
        print(f"   Pending UI tools: {cg.get_pending_ui_tools()}")
        print(f"   State after: {cg.state.to_dict()}\n")
    except Exception as e:
        print(f"[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
    
    # Test template resolution
    print("[TEST] Testing template resolution...")
    cg.state.set("user_name", "John Doe")
    cg.state.set("room_number", 305)
    
    test_template = {
        "greeting": "Hello {{user_name}}",
        "room": "Room {{room_number}}",
        "nested": {
            "message": "Welcome {{user_name}} to room {{room_number}}"
        }
    }
    
    resolved = cg.state.resolve_template(test_template)
    print(f"[OK] Template resolution works")
    print(f"   Input: {test_template}")
    print(f"   Output: {resolved}\n")
    
    # Test plan manipulation
    print("[TEST] Testing plan manipulation...")
    print(f"   Current block index: {cg.plan.current_index}")
    print(f"   Current block: {cg.plan.get_current_block()}")
    
    cg.plan.jump_to(2)
    print(f"   After jump_to(2): {cg.plan.get_current_block()}\n")
    
    # Test adjustments
    print("[TEST] Testing adjustments...")
    cg.state.set("purpose", "Check In")
    fired = cg.adjustments.evaluate(cg.state, cg.plan, cg.tone)
    print(f"   Set purpose='Check In'")
    print(f"   Adjustments fired: {fired}")
    print(f"   New plan index: {cg.plan.current_index}")
    print(f"   New block: {cg.plan.get_current_block()}\n")
    
    print("[SUCCESS] All tests passed!")


if __name__ == "__main__":
    test_basic_flow()

