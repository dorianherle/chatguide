import os
import sys
from chatguide import ChatGuide
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check API key
if "GEMINI_API_KEY" not in os.environ:
    print("Please set GEMINI_API_KEY environment variable in .env file.")
    sys.exit(1)

def print_separator():
    print("-" * 50)

def example_chat():
    print("Initializing ChatGuide...")
    try:
        # Initialize with debug=False for cleaner output
        guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=False)
        guide.load_config("config.yaml")
        
        print("\n" + "="*50)
        print("       WELCOME TO CHATGUIDE EXAMPLE       ")
        print("="*50 + "\n")
        
        # Initial greeting
        reply = guide.chat()
        print(f"Bot: {reply.assistant_reply}")
        
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ['exit', 'quit']:
                    print("\nGoodbye!")
                    break
                
                guide.add_user_message(user_input)
                reply = guide.chat()
                
                print(f"Bot: {reply.assistant_reply}")
                
                # Optional: Show what data was extracted
                if reply.task_results:
                    print("\n[Extracted Data]")
                    for res in reply.task_results:
                        print(f"  - {res.key}: {res.value}")
                
                if guide.is_finished():
                    print("\n" + "="*50)
                    print("       CONVERSATION COMPLETE       ")
                    print("="*50)
                    print("Final State Captured:")
                    for key, value in guide.state.to_dict().items():
                        print(f"  {key}: {value}")
                    break
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    example_chat()
