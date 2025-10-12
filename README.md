<p align="center">
  <img src="static/chatguide.png" alt="ChatGuide" width="800"/>
</p>



<p align="center">
  <strong>A lightweight, modular framework for building goal-oriented conversational AI.</strong>
</p>

<p align="center">
ChatGuide makes it easy to create conversations that have a <strong>purpose</strong>—whether that's tech support triage, user onboarding, lead qualification, or interactive forms. Instead of free-form chats that wander aimlessly, ChatGuide keeps conversations focused while feeling natural and adaptive.
</p>

---

## 🎯 What Makes ChatGuide Different?

Most AI frameworks are built for RAG pipelines or autonomous agents. ChatGuide is built for **guided conversations**—conversations where you know what information you need to collect, but want the AI to handle the dialogue naturally.

**Core Philosophy:**
- **Declarative task flow** – Define what you need, not how to get it
- **Dynamic routing system** – Behavior adapts based on conversation state
- **Separation of data and presentation** – History stored as structured data, rendered dynamically
- **Simple, readable architecture** – The entire core is ~1500 lines you can understand in an hour

---

## ⚡ Quick Start

Let's build a simple tech support bot **step-by-step**. You'll learn how ChatGuide works by seeing each piece in action.

**What we're building:** A bot that collects user info, detects their mood, and adapts its tone automatically.

---

### Step 1: Understand the Config File

The config file is where you tell ChatGuide **what** to collect, **how** to speak, and **when** to adapt.

Create `config.yaml`:

```yaml
# ════════════════════════════════════════════════════════════════
# TASKS: What information to collect
# ════════════════════════════════════════════════════════════════
# Format: task_name: "type, description"
# Types: string (text), int (number), enum (choose from list)

tasks:
  # Information gathering
  get_name: "string, Ask for the user's name"
  get_age: "int, Ask for the user's age"
  get_issue: "string, Ask what problem they're experiencing"
  
  # AI assessment (computed by the LLM)
  assess_severity: "enum, Determine severity. Choose: low, medium, critical"
  
  # Persistent monitoring (runs every turn)
  monitor_mood: "enum, Detect user mood. Choose: happy, frustrated, neutral"
  
  # System task (handles corrections)
  detect_info_updates: "Check if user corrects previous info. Format: 'update: task_id = value' or empty string"

# ════════════════════════════════════════════════════════════════
# TONES: How the AI speaks
# ════════════════════════════════════════════════════════════════

tones:
  helpful: "Be clear, friendly, and solution-focused"
  urgent: "Be direct and prioritize quick resolution"
  empathetic: "Be understanding and supportive"

# ════════════════════════════════════════════════════════════════
# GUARDRAILS: Rules the AI must always follow
# ════════════════════════════════════════════════════════════════

guardrails: "Stay focused on current tasks. If user goes off-topic, gently redirect."

# ════════════════════════════════════════════════════════════════
# ROUTES: When to change behavior
# ════════════════════════════════════════════════════════════════
# Format: condition → action

routes:
  # Critical issue detected → switch to urgent tone
  - condition: "task_results.get('assess_severity') == 'critical'"
    action: "tones.set_tones"
    tones: ["urgent", "empathetic"]
  
  # User frustrated → be empathetic
  - condition: "task_results.get('monitor_mood') == 'frustrated'"
    action: "tones.set_tones"
    tones: ["empathetic"]
  
  # User corrects info → apply correction
  - condition: "'update:' in task_results.get('detect_info_updates', '')"
    action: "process_corrections"
  
  # Name detected → update display name in history
  - condition: "task_results.get('get_name') and task_results.get('get_name') != user_name"
    action: "set"
    path: "participants.user"
    value: "task_results.get('get_name')"
```

**💡 What did we just define?**
- **6 tasks** the bot needs to complete (3 info gathering + 3 monitoring)
- **3 tones** the bot can use (helpful, urgent, empathetic)
- **4 routes** that make the bot adaptive (severity, mood, corrections, name updates)

### Step 2: Write Your Conversation Script

Now we'll wire everything together with code. Each section is explained inline.

Create `main.py`:

```python
from chatguide import ChatGuide
import os

# ════════════════════════════════════════════════════════════════
# INITIALIZE: Create the ChatGuide instance
# ════════════════════════════════════════════════════════════════

guide = ChatGuide(debug=True)  # debug=True shows what's happening

# Load the config file we just created
guide.load_config("config.yaml")

# ════════════════════════════════════════════════════════════════
# DEFINE FLOW: What order to collect information
# ════════════════════════════════════════════════════════════════

guide.set_flow(
    batches=[
        # Batch 0: Start with basics (both must complete before advancing)
        ["get_name", "get_age"],
        
        # Batch 1: Then ask about the problem
        ["get_issue"],
        
        # Batch 2: Finally assess severity
        ["assess_severity"],
    ],
    
    # These tasks run EVERY turn (not just in one batch)
    persistent=["monitor_mood", "detect_info_updates"]
)

# ════════════════════════════════════════════════════════════════
# START: Begin the conversation
# ════════════════════════════════════════════════════════════════

guide.start(
    memory="You're a friendly tech support assistant helping users troubleshoot issues.",
    tones=["helpful"]  # Start with the "helpful" tone
)

print("Tech Support Bot initialized! 🤖\n")

# ════════════════════════════════════════════════════════════════
# CHAT LOOP: Keep talking until all batches complete
# ════════════════════════════════════════════════════════════════

while not guide.state.flow.is_finished():
    user_input = input("You: ")
    
    # 1. Add user's message to history
    guide.add_user_message(user_input)
    
    # 2. Get AI response (this is where the magic happens!)
    reply = guide.chat(
        model="gemini/gemini-2.5-flash-lite",
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # 3. Show the response
    print(f"Bot: {reply.assistant_reply}")

    # 4. Debug info (optional)
    if guide.debug:
        batch = guide.state.flow.current_index
        print(f"[Batch {batch}/3 | Mood: {guide.state.tasks.results.get('monitor_mood', '?')}]\n")

# ════════════════════════════════════════════════════════════════
# DONE: Show what we collected
# ════════════════════════════════════════════════════════════════

print("\n=== Session Complete ===")
results = guide.state.tasks.results
print(f"Name:     {results.get('get_name')}")
print(f"Age:      {results.get('get_age')}")
print(f"Issue:    {results.get('get_issue')}")
print(f"Severity: {results.get('assess_severity')}")
```

**💡 What's happening here?**

1. **Load config** → ChatGuide knows what tasks/tones/routes exist
2. **Set flow** → Defines the order: basics → issue → severity
3. **Start** → Gives the bot context and initial tone
4. **Loop** → Each turn: user input → AI response → update state
5. **Results** → Access all collected info via `state.tasks.results`

### Step 3: Set up environment

```bash
# Create .env file with your API key
echo "GEMINI_API_KEY=your_key_here" > .env
```

Get your Gemini API key: https://aistudio.google.com/app/apikey

### Step 4: Run it!

```bash
python main.py
```

### What's happening under the hood?

**Batch progression:**
1. Bot asks for name and age (Batch 0)
2. Once both are provided → advances to Batch 1
3. Bot asks about the issue (Batch 1)
4. Once issue is provided → advances to Batch 2
5. Bot assesses severity (Batch 2)
6. Done! ✅

**Dynamic routing in action:**
- If user says "I'm so frustrated" → `monitor_mood` detects it → route fires → tone changes to "empathetic"
- If severity is "critical" → route fires → tone changes to "urgent"
- If user corrects their name → `detect_info_updates` detects it → route fires → name updated everywhere

**Example conversation:**

```
You: Hi
Bot: Hey there! I'm here to help with any tech issues. What's your name?
[Debug: Batch 0]

You: I'm Alex
Bot: Nice to meet you, Alex! How old are you?
[Debug: Batch 0]

You: 28
Bot: Got it! So what issue are you experiencing?
[Debug: Batch 1]

You: My app keeps crashing on startup
Bot: That sounds frustrating. Let me assess the severity... This seems like a medium severity issue.
[Debug: Batch 2]

=== Session Summary ===
Name: Alex
Age: 28
Issue: My app keeps crashing on startup
Severity: medium
```

**Try it:** Now change "medium" to "critical" in the conversation and watch the tone shift to urgent! 🔥

---

## 🧩 Architecture Overview

ChatGuide is built around **five core concepts**:

### 1. **State Containers** – The Source of Truth

All conversation state lives in modular containers:

```python
state = ConversationState(
    conversation=Conversation(),    # Memory, history, turn_count
    flow=Flow(),                    # Task batches + progression
    tasks=Tasks(),                  # Task results, status, attempts
    tones=Tones(),                  # Active tones
    routes=Routes(),                # Route execution tracking
    participants=Participants()     # User & chatbot names
)
```

**Container Details:**

| Container | What It Holds | Example Access |
|-----------|---------------|----------------|
| **`conversation`** | Memory context, message history, turn counter | `state.conversation.memory = "You're a support bot"`<br>`state.conversation.turn_count = 5`<br>`state.conversation.history` → list of messages |
| **`flow`** | Task batches, current position, persistent tasks | `state.flow.current_index` → current batch number<br>`state.flow.batches` → all task batches<br>`state.flow.persistent` → always-active tasks |
| **`tasks`** | Results, status, attempt counts per task | `state.tasks.results["get_name"]` → "John"<br>`state.tasks.status["get_name"]` → "completed"<br>`state.tasks.attempts["get_name"]` → 1 |
| **`tones`** | Active tone list | `state.tones.active` → `["friendly", "empathetic"]`<br>`state.tones.set_tones(["urgent"])` |
| **`routes`** | Which routes fired and when | `state.routes.fired_this_turn` → `["route_0"]`<br>`state.routes.last_fired["route_0"]` → 5 |
| **`participants`** | User and chatbot names (dynamic) | `state.participants.user` → "John"<br>`state.participants.chatbot` → "Sol" |

**Key Design Principles:**

1. **Direct Mutation** – No getters/setters, just modify attributes directly
2. **Separation of Concerns** – Each container has one clear responsibility  
3. **Full Observability** – All state is serializable via `state.to_dict()`
4. **Consistent Naming** – Variable name = class name (lowercase)

### 2. **Task Flow** – Sequential Progression

Tasks are organized into **batches** that run in sequence:

```python
guide.set_flow(
    batches=[
        ["get_name"],                      # Batch 0
        ["get_age", "get_location"],       # Batch 1 (parallel)
        ["summarize"]                      # Batch 2
    ],
    persistent=["monitor_mood"]            # Runs in all batches
)
```

**Rules:**
- The AI works on one batch at a time
- All tasks in a batch must complete before advancing
- Persistent tasks run continuously across all batches
- Flow only moves forward (no backtracking)

### 3. **Dynamic Routing** – Behavior Adaptation

Routes trigger actions when conditions are met:

```yaml
routes:
  # Auto-correct user information
  - condition: "'update:' in task_results.get('detect_info_updates', '')"
    action: "process_corrections"
  
  # Update participant name when detected
  - condition: "task_results.get('get_name') and task_results.get('get_name') != user_name"
    action: "set"
    path: "participants.user"
    value: "task_results.get('get_name')"
  
  # Adapt tone to user emotion
  - condition: "task_results.get('monitor_mood') in ['sad', 'frustrated']"
    action: "interaction.set_tones"
    tones: ["empathetic"]
  
  # Force advance after too many attempts
  - condition: "max([task_attempts.get(task, 0) for task in current_tasks]) > 4"
    action: "flow.advance"
    force: true
```

**Available route actions:**
- `set` – Update any state field directly
- `append` – Add to lists or strings
- `process_corrections` – Parse and apply detected corrections
- `{container}.{method}` – Call any container method with params

### 4. **History as Data** – Dynamic Resolution

History is stored as **structured objects**, not strings:

```python
# Storage format
history = [
    {"role": "Human", "text": "My name is Dorian"},
    {"role": "Sol", "text": "Nice to meet you, Dorian!"},
    {"role": "Human", "text": "Actually, I'm John"}
]

# Rendered dynamically when building prompt
# If participants.user = "John", ALL messages show:
John: My name is Dorian
Sol: Nice to meet you, Dorian!
John: Actually, I'm John
```

**Why this matters:**
When a correction route updates `participants.user`, **the entire history automatically reflects the new name** in the next prompt—no manual string replacement needed.

### 5. **Prompt Builder** – Context Assembly

The `PromptBuilder` assembles context from state:

```
MEMORY:
{conversation.memory}
Known info:
- get_name: John
- get_age: 32

CHAT HISTORY:
John: My name is Dorian
Sol: Nice to meet you!
John: Actually, I'm John

CURRENT TASKS:
get_location: Ask where the user currently lives

PERSISTENT TASKS:
monitor_mood: Detect emotional state
detect_info_updates: Check for corrections

TONE: Be friendly and warm
```

---

## 🔄 Request Lifecycle

Here's what happens during a single turn:

```
USER TURN STARTS
        ↓
┌─────────────────────────────────────────────────────────────┐
│  1. User message added to history                           │
│     guide.add_user_message(user_input)                      │
│     → state.conversation.history.append({"role": "Human",   │
│                                          "text": "..."})    │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  2. PromptBuilder assembles context from state              │
│     prompt = PromptBuilder(config, state).build()           │
│                                                             │
│     Reads:                                                  │
│     ├─ state.conversation.memory                            │
│     ├─ state.conversation.history (dynamically resolved)    │
│     ├─ state.tracker.results (Known info section)           │
│     ├─ state.flow.current_batch (CURRENT TASKS)             │
│     └─ state.flow.persistent_tasks (PERSISTENT TASKS)       │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  3. LLM called with structured JSON schema                  │
│     reply = guide.chat(model="gemini/...", api_key=...)     │
│                                                             │
│     Returns:                                                │
│     {                                                       │
│       "tasks": [{"task_id": "...", "result": "..."}],      │
│       "persistent_tasks": [{...}],                          │
│       "assistant_reply": "..."                              │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Process batch tasks                                     │
│     for task in reply.tasks:                                │
│       state.tracker.results[task_id] = result               │
│       state.tracker.status[task_id] = "completed"           │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Process persistent tasks                                │
│     for task in reply.persistent_tasks:                     │
│       state.tracker.results[task_id] = result               │
│                                                             │
│     (includes detect_info_updates with corrections)         │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  6. Execute routes  ⚡ CRITICAL TIMING                      │
│     _process_routes()                                       │
│                                                             │
│     For each route:                                         │
│       ├─ Evaluate condition (RouteEvaluator)                │
│       └─ If true → execute action (RouteExecutor)           │
│                                                             │
│     Examples:                                               │
│     • process_corrections → updates tracker.results         │
│     • set participants.user → updates name                  │
│     • interaction.set_tones → changes tone                  │
│                                                             │
│     🎯 State mutations happen HERE, BEFORE history update   │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  7. Add AI message to history                               │
│     state.conversation.add_message(                         │
│         chatbot,                                            │
│         reply.assistant_reply                               │
│     )                                                       │
│                                                             │
│     ✅ History saved with corrected state                   │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  8. Try to advance flow                                     │
│     if not state.get_current_tasks():                       │
│         state.flow.advance()                                │
│                                                             │
│     (moves to next batch if current is complete)            │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│  9. Return reply to caller                                  │
│     return reply                                            │
└─────────────────────────────────────────────────────────────┘
        ↓
    WAIT FOR NEXT USER INPUT
```

### 🔑 Key Insight: Route Timing

Routes fire **before** the AI message is added to history. This critical ordering ensures:

1. **Corrections apply immediately** – `detect_info_updates` corrections update `tracker.results` before the next prompt
2. **History stays consistent** – Name changes update `participants.user` before rendering the next prompt
3. **No race conditions** – All state mutations complete before history is frozen

**Example:**
```
User: "Actually I'm John" 
→ LLM detects: detect_info_updates = "update: get_name = John"
→ Route fires: process_corrections → tracker.results['get_name'] = 'John'
→ Route fires: set participants.user = 'John'
→ History added: {"role": "Sol", "text": "..."}
→ Next prompt: ALL history shows "John: ..." (dynamically resolved)
```

---

## 📦 Project Structure

```
chatguide/
├── src/chatguide/
│   ├── chatguide.py              # Main orchestrator
│   ├── schemas.py                # Pydantic models
│   │
│   ├── core/
│   │   ├── state.py              # ConversationState
│   │   ├── config.py             # Config container
│   │   └── containers/
│   │       ├── conversation.py   # Memory + history
│   │       ├── task_flow.py      # Batch progression
│   │       ├── task_tracker.py   # Results + status
│   │       ├── interaction.py    # Tones, turn count
│   │       └── participants.py   # User/chatbot names
│   │
│   ├── builders/
│   │   └── prompt.py             # Prompt assembly
│   │
│   ├── routing/
│   │   ├── evaluator.py          # Condition evaluation
│   │   └── executor.py           # Action execution
│   │
│   ├── io/
│   │   ├── llm.py                # LLM interface (litellm)
│   │   └── storage.py            # Save/load state
│   │
│   └── utils/
│       ├── config_loader.py      # YAML parsing
│       ├── response_parser.py    # LLM response parsing
│       └── debug_formatter.py    # Pretty printing
│
└── config.yaml                    # Task definitions + routes
```

**Design Principles:**
- **One responsibility per module** – Easy to understand and test
- **Direct state access** – No hidden getters/setters
- **Dependency injection** – Containers passed explicitly
- **Pure functions where possible** – Formatters, parsers, evaluators

---

## 🚀 Getting Started

### Installation

```bash
# Clone the repo
git clone <your-repo-url>
cd chatguide

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "GEMINI_API_KEY=your_key_here" > .env
```

Get your Gemini API key: https://aistudio.google.com/app/apikey

---

## 🔧 Configuration Reference

### Route Condition Variables

Available in route conditions:

```python
{
    "task_results": dict,           # All completed task results
    "turn_count": int,              # Total conversation turns
    "batch_index": int,             # Current batch number
    "task_attempts": dict,          # Attempts per task
    "current_tasks": list,          # Tasks in current batch
    "user_name": str,               # Current user name
    "chatbot_name": str            # Current chatbot name
}
```

### Route Actions

**Direct field mutation:**
```yaml
- condition: "task_results.get('user_type') == 'premium'"
  action: "set"
  path: "interaction.tones"
  value: ["professional", "concierge"]
```

**Container method calls:**
```yaml
- condition: "turn_count > 10"
  action: "flow.advance"
  force: true
```

**Special actions:**
```yaml
- condition: "'update:' in task_results.get('detect_info_updates', '')"
  action: "process_corrections"
```

---

## 🆚 Comparison

| Feature | ChatGuide | LangChain | Rasa |
|---------|-----------|-----------|------|
| **Purpose** | Guided conversations | General AI pipelines | Intent-based bots |
| **Lines of code** | ~1,500 | 100,000+ | 50,000+ |
| **Dependencies** | 3 | 50+ | 30+ |
| **Learning curve** | 1 hour | Days | Weeks |
| **State management** | Built-in containers | DIY | Tracker stores |
| **Dynamic routing** | Declarative YAML | Custom code | Stories/rules |
| **LLM required** | Yes | Optional | No (NLU) |
| **Best for** | Goal-oriented convos | RAG/agents | Intent classification |

**Use ChatGuide when:**
- You need to collect specific information through conversation
- You want behavior to adapt based on conversation state
- You need clean, readable, maintainable code
- You're building forms, onboarding, triage, or support flows

---

## 💡 Best Practices

### 1. Use persistent tasks for monitoring

```python
persistent=["monitor_mood", "detect_info_updates", "check_engagement"]
```

Persistent tasks run every turn and enable reactive routing.

### 2. Store history as data, not strings

✅ **Good:**
```python
history = [{"role": "user", "text": "..."}]
```

❌ **Bad:**
```python
history = ["User: ..."]
```

This lets you update participant names retroactively.

### 3. Let routes handle mutations

Don't hardcode state changes—use routes:

```yaml
- condition: "task_results.get('get_name') != user_name"
  action: "set"
  path: "participants.user"
  value: "task_results.get('get_name')"
```

### 4. Keep batches focused

```python
# Good - logical grouping
batches=[
    ["get_name", "get_age"],           # Identity
    ["get_issue", "get_severity"],     # Problem
    ["provide_solution"]               # Resolution
]

# Bad - everything in one batch
batches=[
    ["get_name", "get_age", "get_issue", "get_severity", "provide_solution"]
]
```

### 5. Debug with state inspection

```python
state_dict = guide.get_state()
print(f"Batch: {state_dict['flow']['current_index']}")
print(f"Tasks: {state_dict['tracker']['status']}")
print(f"Results: {state_dict['tracker']['results']}")
```

---

## 🐛 Troubleshooting

**Task not completing?**

Check if the LLM is returning empty strings:
```python
reply = guide.chat()
for task in reply.tasks:
    if not task.result:
        print(f"Task {task.task_id} returned empty!")
```

Fix: Make task descriptions more specific.

**Routes not firing?**

Enable debug mode to see route evaluation:
```python
guide = ChatGuide(debug=True)
```

Check logs for: `Route fired: {action}`

**Name not updating in history?**

Ensure you're using the dynamic history format (already implemented if you followed this README).

---

## 📖 API Reference

### ChatGuide Class

```python
guide = ChatGuide(debug=bool, api_key=str)

# Configuration
guide.load_config(path: str)
guide.set_flow(batches: List[List[str]], persistent: List[str])

# Conversation
guide.start(memory: str, tones: List[str])
guide.add_user_message(message: str)
guide.chat(model: str, api_key: str, temperature: float, max_tokens: int) -> ChatGuideReply

# Utilities
guide.get_state() -> dict
guide.get_prompt() -> str
guide.print_debug(show_prompt: bool) -> str
```

### Response Schema

```python
class ChatGuideReply:
    tasks: List[TaskResult]
    persistent_tasks: List[TaskResult]
    assistant_reply: str

class TaskResult:
    task_id: str
    result: str
```

---
