import os
import sys
# Ensure we use the local source code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chatguide import ChatGuide
from chatguide.core.task import Task
from chatguide.core.block import Block
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if "GEMINI_API_KEY" not in os.environ:
    print("Please set GEMINI_API_KEY environment variable in .env file.")
    sys.exit(1)

def verify_refactor():
    print("Initializing ChatGuide...")
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=True)
    
    # Disable console logging to see output clearly
    if guide.logger:
        guide.logger.logger.handlers = []
        
    print("Loading config...")
    guide.load_config("config.yaml")
    
    print("\n--- VERIFICATION: Object Model ---")
    
    # 1. Verify Plan uses Block objects
    first_block = guide.plan._blocks[0]
    if isinstance(first_block, Block):
        print("PASS: Plan uses Block objects.")
    else:
        print(f"FAIL: Plan uses {type(first_block)} instead of Block.")
        
    # 2. Verify Block contains Task objects
    first_task = first_block.tasks[0]
    if isinstance(first_task, Task):
        print("PASS: Block contains Task objects.")
    else:
        print(f"FAIL: Block contains {type(first_task)} instead of Task.")
        
    # 3. Verify Task object attributes
    task_id = first_task.id
    if task_id == "introduce_yourself":
        print("PASS: Task ID is correct.")
    else:
        print(f"FAIL: Task ID is {task_id}, expected 'introduce_yourself'.")
        
    print("\n--- VERIFICATION: Chat Flow ---")
    
    print("Turn 1: Start")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    
    state = guide.get_state()
    current_tasks = state['execution']['current_tasks']
    
    # Verify current_tasks is a list of strings (for API compatibility)
    if isinstance(current_tasks, list) and (not current_tasks or isinstance(current_tasks[0], str)):
         print("PASS: get_state() returns task IDs as strings.")
    else:
         print(f"FAIL: get_state() returns {type(current_tasks)}: {current_tasks}")

    if 'introduce_yourself' in state['progress']['completed_tasks']:
        print("PASS: introduce_yourself completed automatically.")
    else:
        print("FAIL: introduce_yourself NOT completed.")

    print("\n--- Turn 2: User says 'Alex' ---")
    guide.add_user_message("My name is Alex")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    
    state = guide.get_state()
    
    if 'get_name' in state['progress']['completed_tasks']:
        print("PASS: get_name completed.")
    else:
        print("FAIL: get_name NOT completed.")
        
    if state['data'].get('user_name') == 'Alex':
         print("PASS: user_name extracted correctly.")
    else:
         print(f"FAIL: user_name is {state['data'].get('user_name')}")

if __name__ == "__main__":
    verify_refactor()
