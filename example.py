"""Simple ChatGuide example with inline config."""
import sys
sys.path.insert(0, 'python')

from dotenv import load_dotenv
load_dotenv()

import os
from chatguide import ChatGuide

# Define config directly as dict
CONFIG = {
    "plan": [
        ["greet"],
        ["get_name"],
        ["get_age"],
        ["farewell"]
    ],
    "tasks": {
        "greet": {
            "description": "Greet the user warmly",
            "expects": []
        },
        "get_name": {
            "description": "Ask for the user's name",
            "expects": ["name"]
        },
        "get_age": {
            "description": "Ask for the user's age",
            "expects": [{"key": "age", "type": "number", "min": 18, "max": 110}]
        },
        "farewell": {
            "description": "Say goodbye and summarize what you learned",
            "expects": []
        }
    },
    "tone": ["friendly"],
    "tones": {
        "friendly": {"description": "Warm, casual, and helpful"}
    },
    "guardrails": [
        "Never ask for sensitive information like passwords",
        "Keep responses concise"
    ]
}

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Set GEMINI_API_KEY in .env file")
        return
    
    # Pass config dict directly - no temp file needed
    guide = ChatGuide(config=CONFIG, api_key=api_key)
    
    print("=" * 40)
    print("  ChatGuide Example")
    print("=" * 40)
    
    reply = guide.chat()
    print(f"\nBot: {reply.text}\n")
    
    while not guide.is_finished():
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        guide.add_user_message(user_input)
        print("prompt: ", guide._build_prompt())
        reply = guide.chat()
        print(f"\nBot: {reply.text}\n")

        if reply.task_results:
            print("[Extracted]", {r.key: r.value for r in reply.task_results})
            print("[State]", guide.state)
    
    print("\n" + "=" * 40)
    print("Final collected data:")
    for k, v in guide.data.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
