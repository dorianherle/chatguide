import os
import sys
# Ensure we use the local source code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chatguide import ChatGuide
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if "GEMINI_API_KEY" not in os.environ:
    print("Please set GEMINI_API_KEY environment variable in .env file.")
    sys.exit(1)

def test_flow():
    print("Initializing ChatGuide...")
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=True)
    
    # Disable console logging to see output clearly
    if guide.logger:
        guide.logger.logger.handlers = []
        
    guide.load_config("config.yaml")
    
    print("\n--- Turn 1: Start ---")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    
    state = guide.get_state()
    completed = state['progress']['completed_tasks']
    current = state['execution']['current_tasks']
    
    if 'introduce_yourself' in completed:
        print("PASS: introduce_yourself completed automatically.")
    else:
        print("FAIL: introduce_yourself NOT completed.")

    if 'get_name' in current:
        print("PASS: Advanced to get_name block.")
    else:
        print(f"FAIL: Did not advance. Current block: {current}")

    print("\n--- Turn 2: User says 'Alex' ---")
    guide.add_user_message("Alex")
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")
    
    state = guide.get_state()
    completed = state['progress']['completed_tasks']
    
    if 'get_name' in completed:
        print("PASS: get_name completed.")
    else:
        print("FAIL: get_name NOT completed.")
        
    if state['data'].get('user_name') == 'Alex':
         print("PASS: user_name extracted correctly.")
    else:
         print(f"FAIL: user_name is {state['data'].get('user_name')}")

if __name__ == "__main__":
    test_flow()
