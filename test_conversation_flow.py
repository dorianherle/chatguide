#!/usr/bin/env python3
"""Test the conversation flow issues from the user's example."""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue

# Add python directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "python"))

from chatguide import ChatGuide


def simulate_user_conversation():
    """Simulate the exact conversation flow from the user's example."""

    # Create a config similar to what might be used
    config = {
        "plan": [["assess_language"], ["ask_social"]],
        "tasks": {
            "assess_language": {
                "description": "Ask about language fluency in Switzerland",
                "expects": [{"key": "language_fluency", "type": "string"}]
            },
            "ask_social": {
                "description": "Ask about social network in Switzerland",
                "expects": [{"key": "social_network", "type": "string"}]
            }
        },
        "tone": ["friendly"],
        "tones": {"friendly": {"description": "Friendly and conversational"}}
    }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Skipping real LLM test - no GEMINI_API_KEY")
        return

    print("[TEST] Starting conversation flow test...")

    cg = ChatGuide(api_key=api_key, config=config, debug=True)

    # Simulate the conversation from the user's example
    print("\n1. Initial question about language:")
    reply1 = cg.chat()
    print(f"Bot: {reply1.text}")

    # User gives irrelevant response
    print("\n2. User gives irrelevant response:")
    cg.add_user_message("Absolutley horendous")
    reply2 = cg.chat()
    print(f"Bot: {reply2.text}")

    # Check task completion
    current_task = cg._current_task_id()
    is_complete = cg._task_is_complete(current_task)
    print(f"Task '{current_task}' complete: {is_complete}")

    # User gives nonsense response
    print("\n3. User gives nonsense response:")
    cg.add_user_message("I mean i like to smack butts")
    reply3 = cg.chat()
    print(f"Bot: {reply3.text}")

    # Check if it got stuck or progressed
    current_task_after = cg._current_task_id()
    print(f"Current task before: {current_task}, after: {current_task_after}")

    if current_task == current_task_after:
        print("[FAIL] Bot got stuck on same task!")
    else:
        print("[PASS] Bot progressed to next task!")

    # Check final completion status
    is_complete_after = cg._task_is_complete(current_task)
    print(f"Task '{current_task}' marked complete: {is_complete_after}")
    print(f"Task in completed set: {current_task in cg.state['completed']}")

    # Check task results
    print("\nTask results from last response:")
    for tr in reply3.task_results:
        print(f"  {tr.key}: {tr.value}")

    print(f"\nFinal state: {cg.state['data']}")


if __name__ == "__main__":
    simulate_user_conversation()
