"""Minimal terminal chatbot using new ChatGuide architecture."""

import os
from dotenv import load_dotenv
from src.chatguide import ChatGuide

load_dotenv()

def main():
    """Run simple chat loop."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
    
    if not api_key:
        print("ERROR: No API key found. Set GEMINI_API_KEY in .env file")
        return
    
    print("=" * 60)
    print("CHATGUIDE - Simple Terminal Chat")
    print("=" * 60)
    print("Type 'quit' to exit\n")
    
    # Initialize
    cg = ChatGuide(api_key=api_key, debug=False)
    cg.load_config("realistic_hotel_config.yaml")
    
    print(f"Loaded: {len(cg.plan._blocks)} plan blocks, {len(cg.tasks)} tasks\n")
    
    # First message
    print("Assistant: ", end="", flush=True)
    reply = cg.chat()
    print(reply.assistant_reply)
    
    # Show pending UI tools
    pending = cg.get_pending_ui_tools()
    if pending:
        print("\n[UI Tools Available]")
        for tool in pending:
            tool_id = tool.get("tool", "")
            args = tool.get("args", {})
            if "options" in args:
                print(f"  Options: {', '.join(args['options'])}")
    
    print()
    
    # Chat loop
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        # Process message
        cg.add_user_message(user_input)
        reply = cg.chat()
        
        print(f"\nAssistant: {reply.assistant_reply}")
        
        # Show state if changed
        state = cg.state.to_dict()
        changed_state = {k: v for k, v in state.items() if v is not None and v != False and v != ""}
        if changed_state:
            print(f"\n[State: {changed_state}]")
        
        # Show pending UI tools
        pending = cg.get_pending_ui_tools()
        if pending:
            print("\n[UI Tools Available]")
            for tool in pending:
                tool_id = tool.get("tool", "")
                args = tool.get("args", {})
                if "options" in args:
                    print(f"  Options: {', '.join(args['options'])}")
        
        print()


if __name__ == "__main__":
    main()

