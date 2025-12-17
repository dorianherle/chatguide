#!/usr/bin/env python3
"""
Clean conversational chatbot demo
Shows the flow: [PROMPT] -> [BOT] -> [USER] -> repeat until [SIDECAR]
"""

from conversational_chatbot import ConversationalChatbot

def demo():
    """Clean interactive demo"""
    print("Conversational Chatbot Demo")
    print("Flow: [PROMPT] -> [BOT] -> [USER] -> repeat")
    print("Commands: 'status', 'reset', 'quit'")
    print()

    chatbot = ConversationalChatbot()

    # Initial bot greeting (no prompt shown)
    initial_response = chatbot.get_conversation_response("Hello! Let's start chatting.")
    chatbot.state.add_conversation_turn("Hello!", initial_response)

    print("[BOT]", initial_response.replace('\n', ' '))
    print()

    while True:
        # Get user input
        user_input = input("[USER] ").strip()

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'status':
            status = chatbot.get_status()
            print(f"Block: {status['current_block']} | Extracted: {status['extracted_data']} | Missing: {status['missing_required']}")
            continue
        elif user_input.lower() == 'reset':
            chatbot = ConversationalChatbot()
            print("Conversation reset.")
            continue

        # Show current prompt
        missing_fields = [f['name'] for f in chatbot.state.get_missing_fields() + chatbot.state.get_optional_fields()]
        prompt = f"""[PROMPT]
{chatbot.state.main_prompt}

Context: {chatbot.state.get_current_block()['name']} phase
Gathering: {', '.join(missing_fields)}

User: {user_input}
Assistant:"""

        print(prompt)

        # Bot response
        response = chatbot.process_user_message(user_input)
        print("[BOT]", response.replace('\n', ' '))
        print()

if __name__ == "__main__":
    demo()
