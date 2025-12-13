import os
import sys
from pathlib import Path
from chatguide import ChatGuide
from dotenv import load_dotenv

load_dotenv()

def simple_test():
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=False)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "config.yaml"
    guide.load_config(str(config_path))
    
    print("=" * 60)
    print("SIMPLE TEST - Step by step extraction")
    print("=" * 60)
    
    # Step 1
    print("\n[STEP 1] Initial")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    
    # Step 2
    print("\n[STEP 2] User: Yes")
    guide.add_user_message("Yes")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}")
    print(f"Current task: {guide.get_current_task()}")
    
    # Step 3  
    print("\n[STEP 3] User: Dorian")
    guide.add_user_message("Dorian")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}")
    print(f"Current task: {guide.get_current_task()}")
    
    # Step 4
    print("\n[STEP 4] User: 13")
    guide.add_user_message("13")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}")
    print(f"Current task: {guide.get_current_task()}")
    
    # Show task states
    print("\n[TASK STATUS]")
    current_block = guide.plan.get_current_block()
    if current_block:
        for task in current_block.tasks:
            print(f"  {task.id}: {task.status}")
    
    # Step 5
    print("\n[STEP 5] User: Germany")
    guide.add_user_message("Germany")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    print(f"Extracted: {[(r.key, r.value) for r in reply.task_results]}")
    print(f"Current task: {guide.get_current_task()}")
    
    # Show task states
    print("\n[FINAL TASK STATUS]")
    if current_block:
        for task in current_block.tasks:
            print(f"  {task.id}: {task.status}")
    
    print("\n[FINAL STATE]")
    for key, value in guide.state.to_dict().items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    simple_test()

