#!/usr/bin/env python3
"""Test script to show minimal v1 ChatGuide example."""

import sys
from pathlib import Path

# Add python directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "python"))

from chatguide import ChatGuide

def test_prompt_generation():
    """Test and display the prompt generated for minimal v1."""

    # Example config with canonical expects format
    config = {
        "plan": [["get_name"]],
        "tasks": {
            "get_name": {
                "description": "Ask for the user's name",
                "expects": [{"key": "user_name", "type": "string"}]
            }
        },
        "tone": ["friendly"],
        "tones": {
            "friendly": {"description": "Warm and helpful"}
        }
    }

    # Initialize ChatGuide
    cg = ChatGuide(api_key="dummy_key", config=config, debug=True)

    # Get the prompt (this would normally be sent to LLM)
    # We can't actually call chat() without a real API key, so we'll examine the prompt building
    from chatguide.builders.prompt import PromptBuilder, PromptView

    # Build the view
    current_task = cg._make_task("get_name")
    view = PromptView(
        current_task=current_task,
        pending_tasks=[current_task],
        completed_tasks=[],
        state={},
        tone_text="Warm and helpful",
        guardrails="",
        history=[],
        language="en",
        next_block_task=None,
        recent_extractions=[]
    )

    # Build and display the prompt
    prompt_builder = PromptBuilder(view)
    full_prompt = prompt_builder.build()

    print("=" * 80)
    print("MINIMAL V1 CHATGUIDE EXAMPLE")
    print("=" * 80)
    print("\nYAML TASK CONFIG:")
    print("""
tasks:
  get_name:
    description: "Ask for the user's name"
    expects:
      - key: user_name
        type: string
""")

    print("\nGENERATED PROMPT (excerpt):")
    print("-" * 40)

    # Show key parts of the prompt
    lines = full_prompt.split('\n')
    in_response_format = False

    for line in lines:
        if 'RESPONSE FORMAT' in line:
            in_response_format = True
        if in_response_format:
            print(line)
        elif 'MANDATORY EXTRACTION RULES' in line:
            print("\n" + line)
            in_response_format = True

    print("\n" + "=" * 80)
    print("EXPECTED LLM RESPONSE FORMAT:")
    print("""
{
  "assistant_reply": "Hi! What's your name?",
  "task_results": [
    {
      "task_id": "get_name",
      "key": "user_name",
      "value": null
    }
  ],
  "tools": []
}
""")

    print("NOTE: On first call, LLM cannot extract user_name yet, so value=null")
    print("On second call after user responds 'John', value='John'")

if __name__ == "__main__":
    test_prompt_generation()

