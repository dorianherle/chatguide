#!/usr/bin/env python3
"""
Interactive test script for the conversational chatbot
Shows data extraction, prompt changes, and block transitions
"""

import time
from conversational_chatbot import ConversationalChatbot

def print_separator(title: str = ""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print(f"\n{'='*50}")

def show_status(chatbot: ConversationalChatbot):
    """Show current chatbot status"""
    print_separator("CHATBOT STATUS")
    status = chatbot.get_status()

    print(f"📍 Current Block: {status['current_block']}")
    print(f"🔄 Turns in Block: {status['turns_in_block']}")
    print(f"📊 Progress: {status['current_block_index'] + 1}/{status['total_blocks']} blocks")

    if status['extracted_data']:
        print(f"✅ Extracted Data:")
        for key, value in status['extracted_data'].items():
            print(f"   • {key}: {value}")

    if status['missing_required']:
        print(f"❌ Missing Required: {', '.join(status['missing_required'])}")

    if status['optional_available']:
        print(f"➕ Optional Available: {', '.join(status['optional_available'])}")

def interactive_test():
    """Run interactive test with the chatbot"""
    print("🤖 Conversational Chatbot Interactive Test")
    print("This test shows:")
    print("• How data gets extracted from conversation")
    print("• When the sidecar LLM analyzes progress")
    print("• How prompts change to refocus conversation")
    print("• Block transitions when requirements are met")
    print("\nCommands:")
    print("• 'status' - Show current state")
    print("• 'quit' - Exit test")
    print("• 'reset' - Start fresh conversation")

    chatbot = ConversationalChatbot()

    # Sample conversation starters
    sample_messages = [
        "Hi there! My name is Alex and I'm 25 years old.",
        "I'm from New York originally.",
        "I really love blue, it's my favorite color.",
        "My hobby is playing guitar and I enjoy rock music.",
        "For short term goals, I want to learn Spanish.",
        "My long term goal is to start my own business.",
        "What's the weather like today?",
        "Tell me a joke!",
        "Do you have any recommendations for good books?",
    ]

    print_separator("STARTING CONVERSATION")
    show_status(chatbot)

    message_index = 0

    while True:
        if message_index < len(sample_messages):
            suggested = f" [Suggested: '{sample_messages[message_index]}']"
            message_index += 1
        else:
            suggested = ""

        user_input = input(f"\nYou{suggested}: ").strip()

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'status':
            show_status(chatbot)
            continue
        elif user_input.lower() == 'reset':
            chatbot = ConversationalChatbot()
            message_index = 0
            print_separator("CONVERSATION RESET")
            show_status(chatbot)
            continue

        print_separator("PROCESSING")
        print(f"User Input: {user_input}")

        start_time = time.time()
        response = chatbot.process_user_message(user_input)
        processing_time = time.time() - start_time

        print(f"🤖 AI Response: {response}")
        print(f"⏱️  Processing time: {processing_time:.2f}s")

        # Show what changed
        status = chatbot.get_status()
        if status['turns_in_current_block'] > 0:
            print(f"🔄 Turn {status['turns_in_current_block']} in current block")

        print_separator()

def demo_extraction():
    """Demonstrate data extraction capabilities"""
    print_separator("DATA EXTRACTION DEMO")

    chatbot = ConversationalChatbot()

    test_cases = [
        ("My name is Sarah Johnson and I'm 28 years old", "name, age"),
        ("I'm originally from Toronto, Canada", "origin"),
        ("Blue is definitely my favorite color", "favorite_color"),
        ("I love playing basketball as my main hobby", "hobby"),
        ("I prefer jazz music over anything else", "music_genre"),
    ]

    for message, expected in test_cases:
        print(f"\nTesting: '{message}'")
        print(f"Expected extraction: {expected}")

        response = chatbot.process_user_message(message)
        status = chatbot.get_status()

        extracted = status['extracted_data']
        print(f"Actually extracted: {list(extracted.keys())}")

        if extracted:
            for key, value in extracted.items():
                print(f"  • {key}: {value}")

        print("-" * 40)

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Interactive conversation test")
    print("2. Data extraction demo")
    print("3. Run both")

    choice = input("Enter choice (1-3): ").strip()

    if choice == '1':
        interactive_test()
    elif choice == '2':
        demo_extraction()
    elif choice == '3':
        demo_extraction()
        print("\n" + "="*60 + "\n")
        interactive_test()
    else:
        print("Invalid choice. Running interactive test.")
        interactive_test()

