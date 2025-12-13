import os
import sys
from pathlib import Path
from chatguide import ChatGuide
from chatguide.builders.prompt import PromptBuilder
from chatguide.utils.config_loader import load_config_file
from chatguide.schemas import TaskDefinition
from dotenv import load_dotenv

load_dotenv()

def check_prompt():
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=False)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "config.yaml"
    guide.load_config(str(config_path))
    
    # Simulate to get_age step
    guide.chat()  # Initial
    guide.add_user_message("Yes")
    guide.chat()
    guide.add_user_message("Dorian")
    guide.chat()
    
    # Now we're at get_age. Add "13" and show prompt
    print("=" * 80)
    print("PROMPT FOR AGE='13' EXTRACTION")
    print("=" * 80)
    guide.add_user_message("13")
    
    # Build prompt manually
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
    
    print(prompt)
    print("\n" + "=" * 80)
    print("KEY SECTIONS TO CHECK:")
    print("=" * 80)
    print("1. Is 'get_age' the CURRENT TASK?")
    print("2. Does it have the extraction examples?")
    print("3. Is 'get_name' completed?")
    print("4. Does CHAT HISTORY show: user: 13")
    print("5. Does the task description say to extract standalone numbers?")

if __name__ == "__main__":
    check_prompt()

