from chatguide import ChatGuide

#initialize the guide
guide = ChatGuide()
guide.load_from_file("config.yaml")
guide.set_task_flow([
    ["get_name", "get_origin"],
    ["offer_language", "get_location"],
    ["reflect", "suggest"]
], persistent=["get_emotion", "detect_info_updates"])


# fake memory
guide.memory = "You are Sol. You are a friendly and helpful assistant."

# fake chat history
guide.chat_history = [
    "Sol: Hi there! My name is Sol. Tell me are you ready for a really really hard question? ;)",
    "User: Yes ;)",
    "Sol: Great! What is your name?",
    "User: John",
    "Sol: Nice to meet you John! Where are you from?",
    "User: Germany",
]

print(guide.prompt())