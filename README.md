# ChatGuide

**The lightweight framework for building guided conversational AI experiences.**

ChatGuide helps you create conversations that have a **goal**. Instead of free-form chats that go anywhere, ChatGuide keeps conversations on track while feeling natural.

Perfect for: tech support triage, onboarding flows, lead qualification, interactive forms, or any conversation with a purpose.

---

## 🎯 What is ChatGuide?

Imagine you're building a tech support bot where an AI needs to diagnose a user's issue through conversation. You can't just ask "Fill out this form." You need a natural, helpful conversation that:

1. **Guides the user** through troubleshooting steps (issue → device info → attempted fixes)
2. **Adapts its tone** based on issue severity (calm for minor issues, urgent for critical ones)
3. **Tracks progress** so it knows what information it has collected
4. **Escalates smartly** if the issue is critical or can't be resolved

That's what ChatGuide does.

---

## ⚡ Quick Example

Build a tech support bot that adapts to issue severity:

```python
from chatguide import ChatGuide
import os

guide = ChatGuide(api_key=os.getenv("GEMINI_API_KEY"))

# Define tasks
guide.add_task("get_issue", "Ask what problem they're experiencing")
guide.add_task("get_device", "Ask what device/system they're using")
guide.add_task("get_error", "Ask if they see any error messages")
guide.add_task("assess_severity", "Determine severity: low, medium, or critical")

# Define tones and routing
guide.tones = {
    "helpful": "Be clear and solution-focused",
    "urgent": "Be direct and prioritize quick resolution"
}
guide.routes = [{
    "condition": "task_results.get('assess_severity') == 'critical'",
    "action": "change_tone",
    "tones": ["urgent"]
}]

# Set conversation flow
guide.set_task_flow(
    [["get_issue"], ["get_device"], ["get_error"]],
    persistent=["assess_severity"]  # Monitor severity throughout
)

# Start
guide.start_conversation(
    memory="You're a tech support assistant helping users troubleshoot issues.",
    starting_message="Hi! I'm here to help. What issue are you experiencing?",
    tones=["helpful"]
)

# Chat loop
while not guide.state_machine.is_finished():
    user_input = input("You: ")
    guide.add_user_message(user_input)
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")

# Access results
print(guide.task_results)  # {'get_issue': 'App crashed', 'get_device': 'iPhone', ...}
```

**What this shows:**
- ✅ Sequential task flow (issue → device → error details)
- ✅ Persistent monitoring (severity assessed every turn)
- ✅ Dynamic routing (critical issues → urgent tone)
- ✅ All data automatically collected in `task_results`

---

## 🧩 Core Concepts

### 1. **Tasks** – What you want to accomplish

A task is a single piece of information you want or an action you want the AI to complete.

```python
guide.add_task("get_email", "Get the user's email address")
guide.add_task("assess_mood", "Figure out if they're happy, sad, or neutral")
```

**Types of tasks:**
- **Batch tasks**: Complete once, then move on (like getting an email)
- **Persistent tasks**: Always running in the background (like monitoring mood)

### 2. **Task Flow** – The conversation roadmap

Organize tasks into **batches** that run in sequence:

```python
guide.set_task_flow([
    ["get_name", "get_age"],        # Batch 1: Get both at once
    ["get_location"],                # Batch 2: After batch 1 completes
    ["summarize"]                    # Batch 3: Final summary
])
```

The AI won't move to the next batch until **all tasks in the current batch are complete**.

### 3. **Tones** – How the AI speaks

Define different speaking styles:

```python
tones = {
    "friendly": "Be warm and casual, like talking to a friend",
    "empathetic": "Be gentle and understanding",
    "playful": "Use humor and be lighthearted"
}
```

You can change tones during the conversation based on context.

### 4. **Routes** – Dynamic behavior

Routes let you change the conversation flow based on what's happening:

```yaml
routes:
  # If user seems frustrated, become more empathetic
  - condition: "task_results.get('assess_mood') == 'frustrated'"
    action: "change_tone"
    tones: ["empathetic"]
  
  # If a task is taking too long, become persistent
  - condition: "max([task_turn_counts.get(task, 0) for task in current_tasks]) > 3"
    action: "change_tone"
    tones: ["persistent"]
```

### 5. **State Machine** – Under the hood

The state machine is ChatGuide's engine. It ensures conversations progress through defined stages:

```
State 0: [get_issue] ──✓──> State 1: [get_device, get_error] ──✓──> State 2: [diagnose]
```

**How it works:**
- Each batch is a **state**
- Can't advance until **all tasks in current state complete**
- Persistent tasks run across **all states**
- Once a state is complete, **can't go back**

**Example:**
```python
guide.set_task_flow(
    [
        ["get_name"],              # State 0
        ["get_device", "get_os"],  # State 1: Both must complete
        ["diagnose"]               # State 2
    ],
    persistent=["monitor_mood"]    # Runs in all states
)
```

**Check state:**
```python
debug = guide.get_debug_info()
print(f"Current state: {debug['state']}")        # 0, 1, 2...
print(f"Incomplete: {debug['current_tasks']}")   # What's left
print(f"Finished: {debug['is_finished']}")       # All done?
```

---

## 🚀 Getting Started

### Installation

```bash
# Clone the repo
git clone <your-repo-url>
cd chatguide

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

Get your Gemini API key from: https://aistudio.google.com/app/apikey

### Basic Usage

**Option 1: Using a config file**

Create `config.yaml`:

```yaml
tasks:
  get_name: "Ask for the user's name"
  get_origin: "Ask where they're from"
  get_interests: "Ask about their hobbies"

tones:
  friendly: "Be warm, casual, and welcoming"
  curious: "Show genuine interest and ask follow-up questions"

guardrails: "Keep the conversation focused on the current task. If the user goes off-topic, gently redirect them."
```

Then in your code:

```python
from chatguide import ChatGuide
import os

guide = ChatGuide(api_key=os.getenv("GEMINI_API_KEY"))

# Load config
guide.load_from_file("config.yaml")

# Set flow
guide.set_task_flow([
    ["get_name"],
    ["get_origin", "get_interests"]
])

# Start
guide.start_conversation(
    memory="You're interviewing someone to learn about them.",
    starting_message="Hey there! Let's get to know each other. What's your name?",
    tones=["friendly"]
)

# Chat
reply = guide.chat()
print(reply.assistant_reply)
```

**Option 2: Pure Python**

```python
from chatguide import ChatGuide
import os

guide = ChatGuide(api_key=os.getenv("GEMINI_API_KEY"))

# Define tasks
guide.add_task("get_name", "Ask for the user's name")
guide.add_task("get_favorite_color", "Ask what their favorite color is")

# Set flow
guide.set_task_flow([["get_name"], ["get_favorite_color"]])

# Start
guide.start_conversation(
    memory="You're a friendly bot learning about the user.",
    starting_message="Hi! What's your name?",
    tones=["neutral"]
)

# Loop
while not guide.state_machine.is_finished():
    user_input = input("You: ")
    guide.add_user_message(user_input)
    
    reply = guide.chat()
    print(f"Bot: {reply.assistant_reply}")

# See what we collected
print("\nCollected info:")
print(guide.task_results)
```

---

## 📚 Step-by-Step Guide

### Step 1: Understanding Task Results

When a task completes, the result is stored:

```python
guide.add_task("get_name", "Ask for the user's name")

# After the conversation:
# User: "My name is Alex"
# Bot: "Nice to meet you, Alex!"

# Check results:
print(guide.task_results)
# Output: {"get_name": "Alex"}
```

The AI extracts the answer and stores it automatically.

### Step 2: Using Persistent Tasks

Some tasks should always be monitoring:

```python
guide.set_task_flow(
    [
        ["get_name"],
        ["get_age"]
    ],
    persistent=["monitor_mood"]  # Always running
)
```

Every turn, `monitor_mood` updates:
```python
# Turn 1: {"monitor_mood": "neutral"}
# Turn 2: {"monitor_mood": "happy"}
# Turn 3: {"monitor_mood": "frustrated"}
```

### Step 3: Dynamic Routing

Change behavior based on the conversation:

```yaml
routes:
  # User is happy? Be playful
  - condition: "task_results.get('monitor_mood') == 'happy'"
    action: "change_tone"
    tones: ["playful"]
  
  # User is frustrated? Slow down and be empathetic
  - condition: "task_results.get('monitor_mood') == 'frustrated'"
    action: "change_tone"
    tones: ["empathetic"]
```

### Step 4: Accessing Results

```python
# Get specific result
name = guide.task_results.get("get_name")

# Get all results
all_info = guide.task_results

# Check if task is complete
if "get_email" in guide.task_results:
    print("Email collected!")

# Get debug info
debug = guide.get_debug_info()
print(f"Current state: {debug['state']}")
print(f"Tasks completed: {debug['task_status']}")
```

---

## 🎨 Real-World Example: Medical Intake Assistant

```python
from chatguide import ChatGuide
import os

guide = ChatGuide(
    api_key=os.getenv("GEMINI_API_KEY"),
    debug=True  # Enable logging
)

# Load the medical intake config
guide.load_from_file("medical_intake_config.yaml")

# Set up the conversation flow
guide.set_task_flow(
    [
        ["get_name", "get_age"],                    # Basic info
        ["get_symptoms"],                           # Current condition
        ["get_medical_history"],                    # Background
        ["get_medications"],                        # Current meds
        ["assess_urgency", "provide_guidance"]      # Triage & advice
    ],
    persistent=["monitor_pain_level", "detect_corrections"]
)

# Start with an empathetic, professional tone
guide.start_conversation(
    memory="You're a caring medical intake assistant gathering information before a doctor's visit. Be empathetic and thorough.",
    starting_message="Hi! I'm here to help gather some information before your appointment. Let's start with your name?",
    tones=["empathetic", "professional"]
)

# Run the conversation
while not guide.state_machine.is_finished():
    user_input = input("\nYou: ")
    guide.add_user_message(user_input)
    
    reply = guide.chat()
    print(f"\nAssistant: {reply.assistant_reply}")
    
    # Check pain level for urgency
    pain_level = guide.task_results.get("monitor_pain_level")
    if pain_level and int(pain_level) > 7:
        print("[System: High pain level detected, prioritizing urgency assessment...]")

# Generate intake summary
intake = {
    "name": guide.task_results.get("get_name"),
    "age": guide.task_results.get("get_age"),
    "symptoms": guide.task_results.get("get_symptoms"),
    "history": guide.task_results.get("get_medical_history"),
    "medications": guide.task_results.get("get_medications"),
    "urgency": guide.task_results.get("assess_urgency")
}

print("\n=== Intake Summary ===")
print(intake)
```

---

## 🔧 Configuration Reference

### Config File Structure

```yaml
# What the AI should never violate
guardrails: "Stay focused on current tasks. Redirect off-topic questions politely."

# Information to collect
tasks:
  get_name: "string, Ask for the user's name"
  get_age: "int, Ask for the user's age"
  assess_mood: "enum: happy, sad, neutral, frustrated"

# Speaking styles
tones:
  friendly: "Be warm and casual"
  empathetic: "Be gentle and understanding"
  playful: "Use light humor and wit"

# Dynamic behavior rules
routes:
  - condition: "turn_count > 5"
    action: "change_tone"
    tones: ["persistent"]
```

### Available Route Conditions

You can use these variables in route conditions:

- `task_results` – Dict of completed task results
- `turn_count` – Total conversation turns
- `state` – Current batch index
- `current_tasks` – Tasks in current batch
- `task_turn_counts` – How many turns each task has been active

Example conditions:
```yaml
# After 3 turns on a task
"max([task_turn_counts.get(task, 0) for task in current_tasks]) > 3"

# If specific info collected
"task_results.get('get_mood') == 'frustrated'"

# If in a specific batch
"state == 2"

# Combination
"state > 1 and task_results.get('engagement') == 'low'"
```

### Dynamic Route Examples

**Force advance after too many attempts:**
```yaml
- condition: "max([task_turn_counts.get(task, 0) for task in current_tasks]) > 3"
  action: "advance_state"
```

**Jump to specific state (e.g., escalation):**
```yaml
- condition: "task_results.get('assess_severity') == 'critical'"
  action: "jump_to_state"
  target_state: 3  # Jump straight to escalation batch
```

**Add urgent follow-up questions:**
```yaml
- condition: "task_results.get('monitor_pain') == 'severe'"
  action: "insert_batch"
  position: 1  # Insert right after current batch
  tasks: ["assess_emergency", "call_911_if_needed"]
```

**Change entire flow based on user type:**
```yaml
- condition: "task_results.get('user_type') == 'enterprise'"
  action: "change_flow"
  batches: 
    - ["get_company_size"]
    - ["get_budget", "get_timeline"]
    - ["schedule_demo"]
  persistent: ["monitor_engagement"]
```

**Dynamically adjust tone:**
```yaml
- condition: "task_results.get('user_mood') == 'frustrated'"
  action: "add_tone"
  tone: "empathetic"

- condition: "task_results.get('user_mood') == 'happy'"
  action: "remove_tone"
  tone: "serious"
```

**Switch bot personality mid-conversation:**
```yaml
- condition: "task_results.get('issue_type') == 'billing'"
  action: "set_chatbot_name"
  name: "Billing Support Agent"
```

### Available Route Actions

**Tone Management:**
- `change_tone` – Replace all active tones with new ones
  - `tones`: `["tone1", "tone2"]`
- `add_tone` – Add a single tone to active tones
  - `tone`: `"empathetic"`
- `remove_tone` – Remove a tone from active tones
  - `tone`: `"playful"`

**Task Management:**
- `add_task` – Define a new task dynamically
  - `task_id`: `"new_task"`, `description`: `"..."`
- `add_persistent_task` – Add a background monitoring task
  - `task_id`: `"monitor_engagement"`
- `remove_persistent_task` – Stop monitoring a persistent task
  - `task_id`: `"monitor_engagement"`

**State Navigation:**
- `advance_state` – Force skip to next batch (marks incomplete as failed)
- `jump_to_state` – Jump to specific state number
  - `target_state`: `2` (jump to state 2)

**Flow Modification:**
- `change_flow` – Completely replace the conversation flow
  - `batches`: `[["task1"], ["task2"]]`, `persistent`: `["monitor"]`
- `add_batch` – Append a new batch at the end
  - `tasks`: `["task1", "task2"]`
- `insert_batch` – Insert batch at specific position
  - `position`: `1`, `tasks`: `["task1", "task2"]`

**Participants:**
- `set_user_name` – Update user's display name
  - `task_id`: `"get_name"` (gets name from task result)
- `set_chatbot_name` – Change bot's name
  - `name`: `"Dr. Smith"`

**Memory:**
- `update_memory` – Replace entire memory
  - `memory`: `"New context..."`
- `append_memory` – Add to existing memory
  - `text`: `"Additional context..."`

---

## 🎯 Advanced Features

### Multi-Provider Support

Switch between AI providers easily:

```python
# Use Gemini (default)
reply = guide.chat(model="gemini/gemini-2.5-flash-lite")

# Use OpenAI (coming soon)
reply = guide.chat(model="openai/gpt-4")

# Use Anthropic (coming soon)
reply = guide.chat(model="anthropic/claude-3-5-sonnet")
```

### Debug Mode

Enable detailed logging:

```python
guide = ChatGuide(debug=True)

# Creates two log files:
# - chatguide.log: Status updates
# - conversation.log: Full prompts and responses
```

### Custom Validation

Override validation for specific tasks:

```python
class MyGuide(ChatGuide):
    def validate_task_result(self, task_id: str, result: str) -> bool:
        if task_id == "get_email":
            return "@" in result  # Basic email validation
        return True
```

---

## 🏗️ Architecture

ChatGuide is built with clean separation of concerns:

```
src/chatguide/
├── schemas.py           # Data models (Task, TaskResult, ChatGuideReply)
├── state_machine.py     # Task flow state management
├── prompt_builder.py    # Prompt assembly
├── config_loader.py     # YAML/JSON configuration parsing
├── response_parser.py   # LLM response parsing
├── chatguide.py         # Main orchestrator
└── io/
    └── llm.py          # Multi-provider LLM interface
```

**Why this matters:**
- **Each module has one job** – easy to understand and test
- **No hidden magic** – you can read the entire codebase in 30 minutes
- **Easy to extend** – add new providers, parsers, or routing actions
- **No dependencies hell** – only 3 core dependencies

---

## 🆚 ChatGuide vs. LangChain

| Feature | ChatGuide | LangChain |
|---------|-----------|-----------|
| **Purpose** | Guided conversations with goals | General-purpose AI chains |
| **Complexity** | ~500 lines of code | 100,000+ lines |
| **Dependencies** | 3 core dependencies | 50+ dependencies |
| **Learning curve** | 30 minutes | Days/weeks |
| **State management** | Built-in state machine | DIY or complex abstractions |
| **Task tracking** | Native support | Build your own |
| **Best for** | Tech support, onboarding, forms | RAG, agents, complex pipelines |

**Use ChatGuide when:**
- You have a conversation with a clear goal
- You want predictable, debuggable behavior
- You need to track task completion
- You want lightweight, maintainable code

**Use LangChain when:**
- You need RAG, vector stores, or agents
- You need 50+ LLM integrations
- You're building complex AI pipelines

---

## 📖 API Reference

### ChatGuide Class

#### Initialization
```python
guide = ChatGuide(
    debug=bool,           # Enable logging (default: False)
    api_key=str          # LLM API key (optional, can pass per-chat)
)
```

#### Configuration Methods
```python
guide.add_task(key: str, description: str)
guide.load_from_file(path: str)
guide.set_task_flow(batches: List[List[str]], persistent: List[str] = None)
guide.set_chatbot_name(name: str)
guide.set_user_name(name: str)
```

#### Conversation Methods
```python
guide.start_conversation(memory: str, starting_message: str, tones: List[str])
guide.add_user_message(message: str)
guide.chat(model: str = "gemini/gemini-2.5-flash-lite", 
          api_key: str = None,
          temperature: float = 0.6,
          max_tokens: int = 256) -> ChatGuideReply
```

#### Utility Methods
```python
guide.get_debug_info() -> dict
guide.prompt() -> str  # Get current prompt for debugging
```

### Response Schema

```python
class ChatGuideReply:
    tasks: List[TaskResult]              # Completed batch tasks
    persistent_tasks: List[TaskResult]   # Persistent task updates
    assistant_reply: str                 # The AI's message

class TaskResult:
    task_id: str    # Which task
    result: str     # The extracted information
```

---

## 💡 Tips & Best Practices

### 1. Keep tasks focused
❌ **Bad:** `"Get all user information"`  
✅ **Good:** `"Get the user's email address"`

### 2. Use persistent tasks for monitoring
```python
persistent=["monitor_mood", "detect_corrections", "check_engagement"]
```

### 3. Start with simple flows, add complexity later
```python
# Start simple
guide.set_task_flow([["get_name"], ["get_email"]])

# Add complexity as needed
guide.set_task_flow(
    [["get_name"], ["get_email", "get_phone"], ["verify_info"]],
    persistent=["monitor_mood"]
)
```

### 4. Use routes for dynamic behavior
Don't hardcode behavior changes—let routes handle it:

```yaml
routes:
  - condition: "task_results.get('user_type') == 'beginner'"
    action: "change_tone"
    tones: ["empathetic", "encouraging"]
```

### 5. Debug with `get_debug_info()`
```python
info = guide.get_debug_info()
print(f"Current batch: {info['state']}")
print(f"Tasks completed: {info['task_status']}")
print(f"What we know: {info['task_results']}")
```

---

## 🐛 Troubleshooting

### "Task not completing"

Check if the AI is returning empty results:
```python
reply = guide.chat()
for task in reply.tasks:
    print(f"{task.task_id}: '{task.result}'")  # Empty string = not complete
```

**Fix:** Make your task description more specific:
- ❌ "Get info"
- ✅ "Ask for the user's email address and extract it"

### "API key error"

Make sure you have a `.env` file:
```bash
GEMINI_API_KEY=your_actual_key_here
```

Or pass it directly:
```python
guide.chat(api_key="your_key_here")
```

### "State not advancing"

The state only advances when **all tasks in the current batch are complete**:

```python
debug = guide.get_debug_info()
print(f"Current tasks: {debug['current_tasks']}")  # Shows incomplete tasks
print(f"Task status: {debug['task_status']}")      # Shows status of each
```

---

## 🤝 Contributing

ChatGuide is designed to be simple and focused. If you want to contribute:

1. Keep it simple
2. One function = one responsibility
3. No new dependencies unless absolutely necessary
4. Add tests for new features

---

## 📜 License

MIT License - use it however you want!

---

## 🙏 Credits

Built for developers who are tired of over-engineered AI frameworks and just want their conversations to work.

Inspired by the need for something simpler than LangChain for guided conversations.
