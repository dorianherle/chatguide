import os
import sys
from pathlib import Path
from chatguide import ChatGuide
from chatguide.builders.prompt import PromptBuilder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check API key
if "GEMINI_API_KEY" not in os.environ:
    print("Please set GEMINI_API_KEY environment variable in .env file.")
    sys.exit(1)

def show_prompt_at_step(guide, step_name):
    """Show the exact prompt that would be sent to the LLM."""
    print("\n" + "=" * 80)
    print(f"  PROMPT BEING SENT TO LLM - {step_name}")
    print("=" * 80)
    
    # Get current block
    current_block = guide.plan.get_current_block()
    
    # Build the prompt manually to see what's being sent
    from chatguide.utils.config_loader import load_config_file
    
    # Get config path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "config.yaml"
    config_data = load_config_file(str(config_path))
    
    # Get tasks map
    tasks_map = {}
    for task_id, task_data in config_data.get("tasks", {}).items():
        from chatguide.schemas import TaskDefinition
        tasks_map[task_id] = TaskDefinition(
            description=task_data.get("description", ""),
            expects=task_data.get("expects", []),
            tools=task_data.get("tools", []),
            silent=task_data.get("silent", False)
        )
    
    # Get tone definitions
    tone_definitions = config_data.get("tones", {})
    
    # Get guardrails
    guardrails_dict = config_data.get("guardrails", {})
    guardrails = "\n".join([f"{k}: {v}" for k, v in guardrails_dict.items()])
    
    # Get completed task IDs
    completed_ids = [t.id for t in guide.plan.get_all_tasks() if t.is_completed()]
    
    # Build prompt
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
    print("  END OF PROMPT")
    print("=" * 80 + "\n")

def main():
    print("=" * 80)
    print("  PROMPT DEBUGGING TEST")
    print("=" * 80)
    
    # Initialize
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=False)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "config.yaml"
    guide.load_config(str(config_path))
    
    # Step 1: Initial
    print("\n>>> STEP 1: Initial greeting")
    show_prompt_at_step(guide, "INITIAL")
    reply = guide.chat()
    print(f"\nAssistant: {reply.assistant_reply}\n")
    
    # Step 2: User says yes
    print("\n>>> STEP 2: User says 'Yes'")
    guide.add_user_message("Yes")
    show_prompt_at_step(guide, "AFTER 'Yes'")
    reply = guide.chat()
    print(f"\nAssistant: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}\n")
    
    # Step 3: User gives name
    print("\n>>> STEP 3: User says 'Dorian'")
    guide.add_user_message("Dorian")
    show_prompt_at_step(guide, "AFTER 'Dorian'")
    reply = guide.chat()
    print(f"\nAssistant: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}\n")
    
    # Step 4: User gives age
    print("\n>>> STEP 4: User says '13'")
    guide.add_user_message("13")
    show_prompt_at_step(guide, "AFTER '13'")
    reply = guide.chat()
    print(f"\nAssistant: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}\n")
    
    # Step 5: User gives origin - THE PROBLEM CASE
    print("\n>>> STEP 5: User says 'Germany' - THE PROBLEM")
    guide.add_user_message("Germany")
    show_prompt_at_step(guide, "AFTER 'Germany'")
    
    print("\n⚠️  PAY ATTENTION TO THIS PROMPT ABOVE ⚠️")
    print("Check if:")
    print("  1. 'get_origin' task is listed in CURRENT TASKS")
    print("  2. The task is marked as >>> CURRENT TASK <<<")
    print("  3. 'get_name' and 'get_age' are marked as completed")
    print("  4. The CURRENT STATE shows user_name and age")
    print("  5. The CHAT HISTORY shows the conversation correctly\n")
    
    reply = guide.chat()
    print(f"\nAssistant: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}")
    
    # Show task status
    print("\n📋 TASK STATUS AFTER 'Germany':")
    current_block = guide.plan.get_current_block()
    if current_block:
        for task in current_block.tasks:
            status_icon = "✓" if task.is_completed() else "○"
            print(f"  {status_icon} {task.id}: {task.status}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

