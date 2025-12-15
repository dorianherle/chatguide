#!/usr/bin/env python3
"""Test the updated prompt flow for minimal v1."""

import sys
import os
from pathlib import Path

# Add python directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "python"))

from chatguide import ChatGuide
from chatguide.builders.prompt import PromptBuilder, PromptView


def test_prompt_generation():
    """Test the prompt generation with conversational guidance."""

    # Create a test config
    config = {
        "plan": [["get_social"]],
        "tasks": {
            "get_social": {
                "description": "Ask about social network in Switzerland",
                "expects": [{"key": "social_network", "type": "string"}]
            }
        },
        "tone": ["friendly"],
        "tones": {"friendly": {"description": "Friendly and conversational"}}
    }

    api_key = os.getenv("GEMINI_API_KEY") or "dummy_key"
    cg = ChatGuide(api_key=api_key, config=config, debug=False)

    # Simulate conversation history like in the user's example
    cg.state["messages"] = [
        {"role": "assistant", "content": "Okay, Dorian, it sounds like your local language skills are not quite where you'd like them to be. Many people find language learning challenging! Do you have a good social network in Switzerland, or do you find it difficult to connect with people?"},
        {"role": "user", "content": "I mean i like to smack butts"},
        {"role": "assistant", "content": "Okay, Dorian, it sounds like your local language skills are not quite where you'd like them to be. Many people find language learning challenging! Do you have a good social network in Switzerland, or do you find it difficult to connect with people?"},
        {"role": "user", "content": "As I said, I like to smack butts"}
    ]

    # Build the prompt view
    current_task = cg._make_task("get_social")
    view = PromptView(
        current_task=current_task,
        pending_tasks=[current_task],
        completed_tasks=[],
        state=cg.state["data"],
        tone_text="Friendly and conversational",
        guardrails="",
        history=cg.state["messages"],
        language="en",
        next_block_task=None,
        recent_extractions=[]
    )

    # Generate the prompt
    prompt_builder = PromptBuilder(view)
    full_prompt = prompt_builder.build()

    print("=" * 80)
    print("UPDATED PROMPT TEST - HANDLING IRRELEVANT RESPONSES")
    print("=" * 80)

    # Show key sections
    sections = full_prompt.split("\n\n")
    for section in sections:
        if "CONVERSATIONAL STYLE:" in section:
            print("\n" + section[:500] + "..." if len(section) > 500 else section)
        elif "RESPONSE STRATEGY:" in section:
            print("\n" + section)
        elif "RESPONSE GUIDANCE WHEN EXTRACTION FAILS:" in section:
            print("\n" + section)

    print("\n" + "=" * 80)
    print("EXPECTED BEHAVIOR:")
    print("- LLM should NOT repeat 'Okay, Dorian'")
    print("- Should acknowledge 'I like to smack butts' naturally")
    print("- Should rephrase the social network question differently")
    print("- Should output task_results with social_network: null")
    print("=" * 80)


if __name__ == "__main__":
    test_prompt_generation()
