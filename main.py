from .chatguide import ChatGuide
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

guide = ChatGuide(api_key=GEMINI_API_KEY)
guide.load_from_file("config.yaml")
guide.set_task_flow([
    ["get_name", "get_origin"],
    ["offer_language","get_location"],
    ["reflect", "suggest"]
], persistent=["get_emotion", "detect_info_updates"])

starting_message = "Hi there! My name is Sol. Tell me areyou ready for a realy reeealy hard question? ;)"
print(starting_message)

guide.start_conversation(
    memory="You are Sol. You are a friendly and helpful assistant.",
    starting_message=starting_message,
    tones=["neutral"]
)

while not guide.all_done():
    user_input = input("👤 You: ")
    if user_input.lower() in ["quit", "exit"]:
        print("👋 Goodbye!")
        break

    guide.add_to_history("User", user_input)

    print("\n===== FULL PROMPT (DEBUG) =====\n")
    print(guide.prompt())

    reply = guide.chat(model="gemini/gemini-2.5-flash-lite", api_key=GEMINI_API_KEY)
    print(reply)
    print("\n🤖 Assistant:", reply.assistant_reply)
    
    # Show current tasks after potential route execution
    print(f"\n📋 Current tasks: {guide.get_current_tasks()}")
    print(f"📋 Next tasks: {guide.get_next_tasks()}")
    print(f"✅ Completed tasks: {[k for k, v in guide.completed_tasks.items() if v]}")
    print(f"🎭 Active tones: {guide.tones_active}")
    print(f"🔄 Turn count: {guide.turn_count}")
    print(f"🔄 Task turn counts: {dict(guide.task_turn_counts)}")
    print(f"📊 Current batch index: {guide.current_batch_idx}")

    # Check if all tasks are done AFTER processing the reply
    if guide.all_done():
        print("🎯 All tasks completed. Conversation finished.")
        break
