"""Test that shows the RAW LLM responses to diagnose extraction issues."""
import os
import sys
import json
from pathlib import Path
from chatguide import ChatGuide
from chatguide.io.llm import run_llm
from chatguide.builders.prompt import PromptBuilder
from chatguide.utils.config_loader import load_config_file
from chatguide.schemas import TaskDefinition, ChatGuideReply
from dotenv import load_dotenv

load_dotenv()

if "GEMINI_API_KEY" not in os.environ:
    print("Please set GEMINI_API_KEY environment variable in .env file.")
    sys.exit(1)

def test_raw_extraction():
    """Test extraction with raw LLM calls to see exactly what's happening."""
    
    print("=" * 80)
    print("  RAW LLM RESPONSE TEST - GERMANY EXTRACTION")
    print("=" * 80)
    
    # Initialize guide
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=False)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "config.yaml"
    guide.load_config(str(config_path))
    
    # Simulate conversation up to Germany
    guide.chat()  # Initial
    guide.add_user_message("Yes")
    guide.chat()
    guide.add_user_message("Dorian")
    guide.chat()
    guide.add_user_message("13")
    guide.chat()
    
    # Now add Germany and inspect
    print("\n>>> Adding user message: 'Germany'")
    guide.add_user_message("Germany")
    
    # Build the prompt manually
    config_data = load_config_file(str(config_path))
    tasks_map = {}
    for task_id, task_data in config_data.get("tasks", {}).items():
        tasks_map[task_id] = TaskDefinition(
            description=task_data.get("description", ""),
            expects=task_data.get("expects", []),
            tools=task_data.get("tools", []),
            silent=task_data.get("silent", False)
        )
    
    tone_definitions = config_data.get("tones", {})
    guardrails_dict = config_data.get("guardrails", {})
    guardrails = "\n".join([f"{k}: {v}" for k, v in guardrails_dict.items()])
    completed_ids = [t.id for t in guide.plan.get_all_tasks() if t.is_completed()]
    
    prompt = PromptBuilder(
        guide.state,
        guide.plan,
        tasks_map,
        guide.tone,
        tone_definitions,
        guardrails,
        guide.context.get_history_dict(),
        guide.language,
        completed_ids
    ).build()
    
    # Call LLM directly
    print("\n>>> Calling LLM directly...")
    raw_response = run_llm(
        prompt,
        model="gemini/gemini-2.0-flash-exp",
        api_key=os.environ["GEMINI_API_KEY"],
        temperature=0.7,
        max_tokens=4000,
        extra_config={"response_schema": ChatGuideReply.model_json_schema()}
    )
    
    print("\n" + "=" * 80)
    print("  RAW LLM RESPONSE (before parsing)")
    print("=" * 80)
    print(json.dumps(raw_response, indent=2) if isinstance(raw_response, dict) else raw_response)
    
    # Parse it
    from chatguide.utils.response_parser import parse_llm_response
    parsed = parse_llm_response(raw_response)
    
    print("\n" + "=" * 80)
    print("  PARSED RESPONSE")
    print("=" * 80)
    print(f"\nAssistant Reply: {parsed.assistant_reply}")
    print(f"\nTask Results:")
    if parsed.task_results:
        for tr in parsed.task_results:
            print(f"  - key: {tr.key}, value: {tr.value}")
    else:
        print("  (none)")
    
    # Check task status
    print("\n" + "=" * 80)
    print("  TASK STATUS BEFORE PROCESSING")
    print("=" * 80)
    current_block = guide.plan.get_current_block()
    if current_block:
        for task in current_block.tasks:
            print(f"\nTask: {task.id}")
            print(f"  Status: {task.status}")
            print(f"  Expects: {task.expects}")
            print(f"  Completed: {task.is_completed()}")
    
    # Now process the reply
    print("\n>>> Processing reply...")
    import asyncio
    asyncio.run(guide._process_reply(parsed, is_silent=False))
    
    print("\n" + "=" * 80)
    print("  TASK STATUS AFTER PROCESSING")
    print("=" * 80)
    current_block = guide.plan.get_current_block()
    if current_block:
        for task in current_block.tasks:
            print(f"\nTask: {task.id}")
            print(f"  Status: {task.status}")
            print(f"  Expects: {task.expects}")
            print(f"  Completed: {task.is_completed()}")
            if task.result:
                print(f"  Result: {task.result}")
    
    print("\n" + "=" * 80)
    print("  STATE AFTER PROCESSING")
    print("=" * 80)
    for key, value in guide.state.to_dict().items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("  DIAGNOSIS")
    print("=" * 80)
    
    # Check if origin was extracted
    if parsed.task_results:
        origin_extracted = any(tr.key == "origin" for tr in parsed.task_results)
        if origin_extracted:
            print("[OK] LLM extracted 'origin' field")
            origin_value = next(tr.value for tr in parsed.task_results if tr.key == "origin")
            print(f"  Value: {origin_value}")
        else:
            print("[FAIL] LLM did NOT extract 'origin' field")
            print("  Keys extracted:", [tr.key for tr in parsed.task_results])
    else:
        print("[FAIL] NO task_results in LLM response")
    
    # Check task completion
    get_origin_task = guide.plan.get_task("get_origin")
    if get_origin_task:
        if get_origin_task.is_completed():
            print("[OK] get_origin task marked as completed")
        else:
            print("[FAIL] get_origin task NOT completed")
            print(f"  Task status: {get_origin_task.status}")
    
    # Check state
    state_dict = guide.state.to_dict()
    if "origin" in state_dict:
        print(f"[OK] 'origin' in state: {state_dict['origin']}")
    else:
        print("[FAIL] 'origin' NOT in state")
        print(f"  State keys: {list(state_dict.keys())}")

if __name__ == "__main__":
    try:
        test_raw_extraction()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

