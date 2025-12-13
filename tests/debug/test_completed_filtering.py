import os
from pathlib import Path
from chatguide import ChatGuide
from chatguide.builders.prompt import PromptBuilder
from chatguide.utils.config_loader import load_config_file
from chatguide.schemas import TaskDefinition
from dotenv import load_dotenv

load_dotenv()

def test_filtering():
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=False)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "config.yaml"
    guide.load_config(str(config_path))
    
    # Progress through conversation
    guide.chat()  # Initial
    guide.add_user_message("Yes")
    guide.chat()
    guide.add_user_message("Dorian")
    guide.chat()
    guide.add_user_message("13")
    guide.chat()
    
    # Now at get_origin. Check if get_name and get_age are in prompt
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
    
    print("=" * 80)
    print("COMPLETED TASK FILTERING TEST")
    print("=" * 80)
    print(f"\nCompleted task IDs: {completed_ids}")
    
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
    
    # Check if completed tasks appear in prompt
    print("\nChecking prompt for completed tasks:")
    print(f"  'get_name' in prompt: {'get_name' in prompt}")
    print(f"  'get_age' in prompt: {'get_age' in prompt}")
    print(f"  'get_origin' in prompt: {'get_origin' in prompt}")
    
    # Extract just the CURRENT TASKS section
    if "CURRENT TASKS:" in prompt:
        tasks_section = prompt.split("CURRENT TASKS:")[1].split("TONE:")[0]
        print("\n" + "=" * 80)
        print("CURRENT TASKS SECTION:")
        print("=" * 80)
        print(tasks_section)

if __name__ == "__main__":
    test_filtering()

