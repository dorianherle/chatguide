"""Test recognize_returning adjustment with silent tasks."""

import os
from dotenv import load_dotenv
from src.chatguide import ChatGuide

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
    if not api_key:
        print("ERROR: No API key")
        return
    
    print("="*70)
    print("TEST: Recognize Returning Guest")
    print("="*70)
    
    cg = ChatGuide(api_key=api_key, debug=False)
    cg.load_config("realistic_hotel_config.yaml")
    
    # 1. Initial state
    print(f"\n1. INIT   | Tone: {cg.tone} | Block: {cg.plan.get_current_block()}")
    
    # 2. Check-in selection
    cg.state.set("purpose", "Check In")
    fired = cg.adjustments.evaluate(cg.state, cg.plan, cg.tone)
    print(f"2. SELECT | Adjustments: {fired} | Block: {cg.plan.get_current_block()}")
    
    # 3. User provides name
    print(f"3. INPUT  | 'My name is John Smith'")
    cg.add_user_message("My name is John Smith")
    
    try:
        # 4. LLM processing (silent task + greeting with adjusted tone)
        reply = cg.chat()
        
        print(f"\n4. RESULT | Tone: {cg.tone}")
        print(f"          | Adjustments: {cg.get_last_fired_adjustments()}")
        print(f"          | State: {cg.state.to_dict()}")
        
        print(f"\n5. REPLY:")
        print(f"   {reply.assistant_reply}")
        
        # Verify
        print("\n" + "-"*70)
        checks = [
            ("Name extracted", cg.state.get("user_name") == "John Smith"),
            ("is_returning_guest", cg.state.get("is_returning_guest") == True),
            ("Tone changed", "returning_guest" in cg.tone),
            ("Adjustment fired", "recognize_returning" in cg.get_last_fired_adjustments()),
            ("Excited reply", "!" in reply.assistant_reply),
            ("Mentions returning", any(w in reply.assistant_reply.lower() for w in ["back", "remember", "again"]))
        ]
        
        for check, passed in checks:
            print(f"  {'✓' if passed else '✗'} {check}")
        
        print("\n" + "="*70)
        print("SUCCESS!" if all(p for _, p in checks) else "PARTIAL")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()
