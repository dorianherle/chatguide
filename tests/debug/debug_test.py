import os
import sys
import json
from pathlib import Path
from chatguide import ChatGuide
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check API key
if "GEMINI_API_KEY" not in os.environ:
    print("Please set GEMINI_API_KEY environment variable in .env file.")
    sys.exit(1)

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def debug_test():
    print_section("INITIALIZING CHATGUIDE")
    
    # Initialize with debug=True
    guide = ChatGuide(api_key=os.environ["GEMINI_API_KEY"], debug=True)
    
    # Get config path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    config_path = project_root / "configs" / "config.yaml"
    guide.load_config(str(config_path))
    
    print("\n✓ ChatGuide initialized")
    print(f"✓ Config loaded from: {config_path}")
    
    # Test conversation
    test_inputs = [
        ("Initial greeting", None),
        ("Respond 'Yes'", "Yes"),
        ("Give name 'Dorian'", "Dorian"),
        ("Give age '13'", "13"),
        ("Give origin 'Germany'", "Germany"),
    ]
    
    for step, (description, user_input) in enumerate(test_inputs, 1):
        print_section(f"STEP {step}: {description}")
        
        if user_input:
            print(f"\n📥 USER INPUT: {user_input}")
            guide.add_user_message(user_input)
        
        # Get response
        print("\n⏳ Calling LLM...")
        reply = guide.chat()
        
        # Show assistant reply
        print(f"\n🤖 ASSISTANT REPLY:")
        print(f"   {reply.assistant_reply}")
        
        # Show extracted data
        print(f"\n📊 EXTRACTED DATA:")
        if reply.task_results:
            for res in reply.task_results:
                print(f"   - {res.key}: {res.value}")
        else:
            print("   (none)")
        
        # Show current state
        print(f"\n💾 CURRENT STATE:")
        state_dict = guide.state.to_dict()
        if state_dict:
            for key, value in state_dict.items():
                print(f"   - {key}: {value}")
        else:
            print("   (empty)")
        
        # Show current block and tasks
        current_block = guide.plan.get_current_block()
        if current_block:
            print(f"\n📋 CURRENT BLOCK TASKS:")
            for task in current_block.tasks:
                status = "✓" if task.is_completed() else "○"
                print(f"   {status} {task.id}")
                print(f"      expects: {task.expects}")
                print(f"      status: {task.status}")
                if task.result:
                    print(f"      result: {task.result}")
        
        # Show execution state
        print(f"\n⚙️  EXECUTION STATE:")
        print(f"   completed tasks: {guide.execution.completed}")
        print(f"   current task: {guide.get_current_task()}")
        print(f"   is finished: {guide.is_finished()}")
        
        # Show plan progress
        print(f"\n📈 PLAN PROGRESS:")
        print(f"   current block index: {guide.plan.current_index}")
        print(f"   total blocks: {len(guide.plan._blocks)}")
        
        # Stop if conversation is finished
        if guide.is_finished():
            print_section("CONVERSATION COMPLETE")
            break
    
    print_section("FINAL STATE")
    print("\n📊 All collected data:")
    for key, value in guide.state.to_dict().items():
        print(f"   {key}: {value}")
    
    print("\n✓ Test completed successfully")

if __name__ == "__main__":
    try:
        debug_test()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

