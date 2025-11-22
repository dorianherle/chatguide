# ChatGuide

![ChatGuide](src/chatguide/static/chatguide.png)

Build conversational AI that actually knows where it is in the conversation.

ChatGuide manages your conversation flow and state so you can focus on building great experiences. Define your conversation in YAML, let the LLM handle language understanding, and get automatic progress tracking, session persistence, and real-time updates out of the box.

## Quick Example

**Define your flow in YAML:**
```yaml
plan:
  - [greet]
  - [get_name, get_email]
  - [confirm]

tasks:
  greet:
    description: "Welcome the user warmly"
  
  get_name:
    description: "Ask for and extract the user's name"
    expects: ["user_name"]
  
  get_email:
    description: "Ask for and extract email"
    expects: ["email"]
  
  confirm:
    description: "Confirm the collected information"
```

**Run it in Python:**
```python
from chatguide import ChatGuide
import os

# One-line initialization
cg = ChatGuide(
    api_key=os.environ["GEMINI_API_KEY"],
    config="config.yaml"
)

# Start conversation
reply = cg.chat()
print(reply.text)  # "Hi! Welcome..."

# User responds
cg.add_user_message("I'm John")
reply = cg.chat()
print(reply.text)  # "Nice to meet you John! What's your email?"

# Check progress anytime
print(cg.get_progress())  # {"completed": 2, "total": 4, "percent": 50}

# Access state with Pythonic syntax
print(cg.state.user_name)  # "John"
print(cg.state.variables)  # {"user_name": "John"}
```

That's it. No conversation state management, no progress tracking, no session handling—it's all automatic.

## What You Get

- **4-Layer Data Architecture** - Clean separation: Variables, Context, Execution, Audit
- **Pythonic State Access** - `state.user_name` instead of `state.get("user_name")`
- **Session Persistence** - Save and restore with `dump()` / `load()`
- **Progress Tracking** - Know exactly where you are in any conversation
- **Real-Time Updates** - Stream events for live UI updates
- **Audit Trail** - Searchable history of all state changes
- **Reactive Flows** - Conversation adjusts based on extracted data
- **Metrics Built-in** - Track LLM calls, tokens, timing, errors
- **Production Ready** - Structured logging, error tracking, middleware hooks

```bash
pip install -e .
```

Set your API key:
```bash
export GEMINI_API_KEY=your_key_here
```

Run the example:
```bash
python example_chat.py
```

## Core Concepts

### State (Variables)
Pythonic access to your business data:
```python
# Pythonic (recommended)
state.user_name = "John"
print(state.user_name)  # "John"

# Traditional (still works)
state.set("user_name", "John")
state.get("user_name")  # "John"

# Get all variables
state.variables  # {"user_name": "John", ...}
```

Use `{{templates}}` anywhere:
```yaml
tools:
  - tool: send_email
    args:
      to: "{{user_email}}"
      subject: "Hello {{user_name}}"
```

### Plan
Ordered sequence of task blocks:
```yaml
plan:
  - [greet, collect_info]    # Block 0
  - [process_payment]        # Block 1
  - [finalize]              # Block 2
```

Manipulate dynamically:
```python
plan.jump_to(2)                    # Jump to block 2
plan.insert_block(1, [new_task])   # Insert new block
plan.remove_block(1)               # Remove block
```

### Tasks
LLM reasoning units that extract data.

The `expects` list defines **which state keys** the task should populate. This tells the LLM exactly what data to look for and what variable name to assign it to.

```yaml
tasks:
  collect_name:
    description: "Ask for the user's name and extract it"
    expects: ["user_name"]  # <--- Will save result to state.get("user_name")
    silent: false
```

**Silent tasks** collect data without showing a reply:
```yaml
extract_name:
  description: "Extract user_name from their message"
  expects: ["user_name"]
  silent: true  # No reply shown, immediate next task
```

When a task completes, it updates the state with the extracted value:
```json
{
  "task_id": "collect_name",
  "key": "user_name",   # Matches one of the keys in 'expects'
  "value": "John Smith"
}
```

### Tools
Deterministic actions (UI, API, functions):
```yaml
tools:
  html.button_choice:
    type: ui
    description: "Display clickable buttons"
  
  send_email:
    type: api
    description: "Send email via API"
```

Tools execute automatically and write results to state.

### Adjustments
Reactive rules watching state:
```yaml
adjustments:
  - name: recognize_returning
    when: state.get("user_name") is not None
    actions:
      - type: state.set
        key: is_returning_guest
        value: true
      - type: tone.set
        tones: ["excited", "welcoming"]
      - type: plan.insert_block
        index: 2
        tasks: [offer_upgrade]
```

Actions available:
- `plan.jump_to` - Jump to block
- `plan.insert_block` - Insert tasks
- `plan.remove_block` - Remove block
- `tone.set` - Replace tone
- `tone.add` - Add tone
- `state.set` - Set state variable

### Tone
Expression style layer (never affects logic):
```yaml
tones:
  professional:
    description: "Clear, courteous, efficient"
  
  excited:
    description: "Use exclamation marks!!! Be enthusiastic!"

tone:
  - professional  # Initial tone
```

## Configuration Example

```yaml
# Hotel receptionist that recognizes returning guests
state:
  user_name: null
  is_returning_guest: false

plan:
  - [greet]
  - [extract_name, welcome_guest, check_in]
  - [complete]

tasks:
  greet:
    description: "Welcome to the hotel"
  
  extract_name:
    description: "Extract user_name from message"
    expects: ["user_name"]
    silent: true  # Extract silently
  
  welcome_guest:
    description: "Greet {{user_name}} warmly"
  
  check_in:
    description: "Process check-in"
    tools:
      - tool: html.card_swipe
        args: {}

tools:
  html.card_swipe:
    type: ui
    description: "Show card swipe animation"

adjustments:
  - name: recognize_returning
    when: state.get("user_name") is not None
    actions:
      - type: state.set
        key: is_returning_guest
        value: true
      - type: tone.set
        tones: ["excited"]

tones:
  excited:
    description: "Very enthusiastic! Use exclamations!"

tone:
  - professional
```

## How It Works

### Runtime Loop

```python
for block in plan:
    for task in block:
        # 1. LLM reasoning
        reply = llm(task.description, state)
        state.update(reply.task_results)
        
        # 2. Execute tools
        for tool in task.tools:
            args = resolve_templates(tool.args, state)
            output = execute_tool(tool, args)
            state.update(output)
        
        # 3. Evaluate adjustments
        adjustments.evaluate(state, plan, tone)
```

### Silent Tasks Magic

Problem: Adjustment fires AFTER LLM response, so tone change comes too late.

Solution: Silent tasks!

```yaml
plan:
  - [extract_name, greet_guest]  # Both in same block

tasks:
  extract_name:
    silent: true  # Collect data, no reply
  
  greet_guest:
    description: "Greet warmly"
```

Flow:
1. User: "My name is John"
2. **LLM Call #1**: Extract name (silent, no reply shown)
3. **Adjustment fires**: tone → "excited"
4. **LLM Call #2**: Greet with new tone
5. Result: "Oh my goodness, John! Welcome back!!!"

## Example Usage

```python
from chatguide import ChatGuide
import os

# Initialize with config
cg = ChatGuide(
    api_key=os.environ["GEMINI_API_KEY"],
    config="config.yaml"
)

# Chat
reply = cg.chat()
print(reply.text)  # Shorter alias for assistant_reply

# Add user message
cg.add_user_message("My name is John")
reply = cg.chat()

# Access state with Pythonic syntax
print(cg.state.user_name)  # "John"
print(cg.state.variables)  # {'user_name': 'John', ...}

# Access the 4 data layers
print(cg.execution.status)  # "awaiting_input"
print(cg.execution.completed)  # ["greet", "get_name"]
print(cg.context.history)  # List of Message objects
print(cg.audit.search(key="user_name"))  # Change history

# Get comprehensive execution state
state = cg.get_state()
print(state['execution']['status'])  # "awaiting_input"
print(state['progress']['completed_count'])  # 2
print(state['data_coverage']['coverage_percent'])  # 25%

# Quick progress check
progress = cg.get_progress()
print(f"{progress['completed']}/{progress['total']} ({progress['percent']}%)")

# Session persistence (4-layer export)
full_data = cg.dump()
# {"variables": {...}, "context": {...}, "execution": {...}, "audit": [...]}
cg.save_checkpoint("session.json")

# Later: restore
cg2 = ChatGuide.load_checkpoint("session.json", api_key="key")

# Streaming for real-time UIs
def on_event(event):
    print(f"Event: {event['type']}")
cg.add_stream_callback(on_event)

# Middleware for custom logic
def log_middleware(context):
    print(f"Processing task: {context['current_task']}")
    return context
cg.add_middleware(log_middleware)

# Task hooks
def on_name_collected(task_id, value):
    print(f"Name collected: {value}")
cg.add_task_hook("get_name", on_name_collected)

# Metrics
metrics = cg.get_metrics()
print(f"LLM calls: {metrics['llm_calls']}")
```

## Data Architecture

ChatGuide uses a **4-layer data model** for clean separation and scalability:

### 1. Variables (`state`)
Business logic data extracted during conversation.
```python
cg.state.user_name  # Pythonic access
cg.state.variables  # Get all: {"user_name": "John", ...}
```

### 2. Context (`context`)
Conversation history and session metadata.
```python
cg.context.history  # List of Message objects
cg.context.session_id  # "abc123"
```

### 3. Execution (`execution`)
Flow control and progress tracking.
```python
cg.execution.status  # "awaiting_input"
cg.execution.completed  # ["greet", "get_name"]
cg.execution.progress(total_tasks=5)  # {"completed": 2, "percent": 40}
```

### 4. Audit (`audit`)
Searchable change history.
```python
cg.audit.search(key="user_name")
# [{"timestamp": "...", "task": "get_name", "old": null, "new": "John"}]
```

**Export all layers:**
```python
full_data = cg.dump()
# {"variables": {...}, "context": {...}, "execution": {...}, "audit": [...]}
```

## Architecture Principles

1. **4-Layer Separation** - Variables, Context, Execution, Audit
2. **Pythonic Access** - `state.var` instead of `state.get("var")`
3. **Tasks are LLM-driven** - Reasoning, language, decisions
4. **Tools are runtime-driven** - Deterministic actions
5. **Args resolved from state** - `{{var}}` templates
6. **Adjustments control reactivity** - Watch state, modify plan/tone
7. **Audit everything** - Full change history for debugging
8. **Tone never affects logic** - Purely expressive

## Project Structure

```
chatguide/
├── src/chatguide/           # Main package
│   ├── chatguide.py         # Main orchestrator
│   ├── state.py             # State management
│   ├── plan.py              # Flow control
│   ├── adjustments.py       # Reactive rules
│   ├── schemas.py           # Pydantic models
│   ├── tool_executor.py     # Tool execution
│   ├── builders/            # Prompt builders
│   │   └── prompt.py
│   ├── io/                  # LLM & storage
│   │   ├── llm.py
│   │   └── storage.py
│   ├── tools/               # Tool implementations
│   │   └── html/
│   └── utils/               # Utilities
│       ├── config_loader.py
│       ├── logger.py
│       └── response_parser.py
│
├── tests/                   # Test suite
│   └── __init__.py
│
├── examples/                # Example implementations
│   ├── streamlit_demo.py    # Interactive web UI
│   └── hotel_config.yaml    # Example configuration
│
├── README.md                # Documentation
├── .gitignore               # Git ignore rules
└── pyproject.toml          # Package configuration
```

## Testing

**Comprehensive test suite validates all 10/10 features:**

```bash
# Run all tests (30 tests covering all features)
pytest tests/

# Run with coverage report
pytest tests/ --cov=chatguide --cov-report=term-missing

# Run specific test file
pytest tests/test_comprehensive.py -v

# Run Streamlit demo
streamlit run examples/streamlit_demo.py
```

**Test Coverage:**
- ✅ State management & templates
- ✅ Plan manipulation & flow control
- ✅ Comprehensive state inspection
- ✅ Helper methods (get_progress, get_current_task, etc.)
- ✅ Session persistence (checkpoint/resume)
- ✅ Streaming callbacks
- ✅ Metrics & telemetry
- ✅ Middleware & hooks
- ✅ Error tracking
- ✅ Config loading
- ✅ Full workflow integration

## Advanced Features

### State Inspection

ChatGuide provides **professional-grade state visibility** for production backends and UIs.

**Get comprehensive execution state:**
```python
state = cg.get_state()
# Returns complete snapshot:
{
  "execution": {
    "current_block_index": 2,
    "current_tasks": ["get_age"],
    "is_finished": False,
    "status": "awaiting_input",  # idle | processing | awaiting_input | complete
    "pending_ui_tools": [],
    "waiting_for_tool": None,
    "errors": [],
    "error_count": 0,
    "retry_count": 0
  },
  "progress": {
    "completed_tasks": ["greet", "get_name"],
    "pending_tasks": ["get_age", "get_location", "payment"],
    "total_tasks": 5,
    "completed_count": 2,
    "blocks": [
      {"index": 0, "tasks": ["greet"], "status": "completed", "completed": True},
      {"index": 1, "tasks": ["get_name", "get_age"], "status": "in_progress", "completed": False}
    ]
  },
  "tasks": {
    "get_name": {
      "status": "completed",
      "description": "Get user's name",
      "expects": ["user_name"],
      "has_tools": False,
      "tool_count": 0,
      "is_silent": False
    },
    "get_age": {
      "status": "in_progress",
      "description": "Get user's age",
      "expects": ["age"],
      "has_tools": False,
      "tool_count": 0,
      "is_silent": False
    }
  },
  "data": {"user_name": "John"},
  "data_extractions": {
    "user_name": {
      "value": "John",
      "extracted_by": "get_name",
      "validated": True
    }
  },
  "data_coverage": {
    "expected_keys": ["user_name", "age", "location", "payment_method"],
    "collected_keys": ["user_name"],
    "missing_keys": ["age", "location", "payment_method"],
    "coverage_percent": 25
  },
  "tone": ["professional"],
  "adjustments": {
    "fired": ["recognize_returning"],
    "all": {...}
  },
  "conversation": {
    "turn_count": 3,
    "user_message_count": 2,
    "assistant_message_count": 1,
    "last_user_message": "My name is John",
    "last_assistant_message": "Great! How old are you?"
  },
  "last_response": {
    "task_results": [{"task_id": "get_name", "key": "user_name", "value": "John"}],
    "tools_called": [],
    "was_silent": False,
    "assistant_reply": "Great! How old are you?"
  }
}
```

**Helper methods:**
```python
# Current task
cg.get_current_task()  # "get_age"

# Progress metrics
cg.get_progress()
# {"completed": 2, "total": 8, "percent": 25, "current_task": "get_age"}

# Upcoming tasks
cg.get_next_tasks(limit=3)  # ["get_location", "payment", "confirm"]

# Check status
cg.is_waiting_for_user()  # True
cg.is_finished()  # False
```

### Template Resolution
```python
state.set("name", "John")
state.set("room", 305)

template = {
    "greeting": "Hello {{name}}",
    "room": "Room {{room}}"
}

resolved = state.resolve_template(template)
# {'greeting': 'Hello John', 'room': 'Room 305'}
```

### Dynamic Plan Modification
```python
# Adjustments can modify the plan mid-conversation
adjustments:
  - name: vip_upgrade
    when: state.get("is_vip") == true
    actions:
      - type: plan.insert_block
        index: 2
        tasks: [offer_suite_upgrade, champagne_service]
```

### Tone Combinations
```yaml
tone:
  - professional
  - empathetic

# Adjustments can change tone
actions:
  - type: tone.set
    tones: ["excited", "grateful"]
```

## Tips

1. **Keep tasks focused** - One responsibility per task
2. **Use silent tasks** - For data extraction before responses
3. **Adjustments for reactivity** - Not hardcoded in tasks
4. **Templates everywhere** - `{{var}}` in tools, descriptions
5. **Monitor state** - Use `get_state()` for complete visibility
6. **Track coverage** - Check `data_coverage` to ensure all expected keys are collected
7. **Test incrementally** - Use test files to verify behavior

## Multi-Language Support

ChatGuide supports 9 languages out of the box:
- English (en) - default
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Chinese (zh)
- Japanese (ja)
- Korean (ko)

**Set language in config:**
```yaml
language: "es"  # Spanish
```

**Or in code:**
```python
cg = ChatGuide(api_key="key", language="fr")  # French
```

Language templates are in `src/chatguide/core/core_prompt.yaml`.

## Examples

See `examples/` directory for complete implementations:

### Hotel Receptionist (`examples/hotel_config.yaml`)
- Multi-path conversation (check-in, check-out, inquiries)
- Silent tasks for name extraction
- Returning guest recognition
- Tone changes based on state
- UI tools (button choices, card swipe animation)

### Interactive Demo (`examples/streamlit_demo.py`)
```bash
streamlit run examples/streamlit_demo.py
```
Full-featured web UI showcasing all ChatGuide capabilities.

## Architecture

**Core Principles:**
1. **State as single source of truth** - All data flows through centralized state
2. **LLM for reasoning** - Tasks handle language understanding and extraction
3. **Runtime for execution** - Tools execute deterministic actions
4. **Reactive adjustments** - Rules watch state and modify flow dynamically
5. **Tone for expression** - Separates style from logic

**Design Philosophy:**
- Declarative over imperative
- Explicit over implicit  
- Composition over inheritance
- Simple over clever

## When to Use

**Good fit:**
- Guided conversations with clear structure
- Multi-step workflows requiring state tracking
- Flows that need dynamic branching
- Conversations requiring session persistence
- UIs needing real-time progress updates

**Not ideal for:**
- Simple Q&A (use RAG/retrieval instead)
- Open-ended conversations (no guided structure needed)
- Complex multi-agent systems (consider agent frameworks)

## API Reference

**Copy this into your LLM chat to get coding help:**

```
ChatGuide API Reference:

Core Classes:
- ChatGuide(api_key=None, config=None, debug=False, language="en", log_format="json", log_file=None)
  - config: Optional path to YAML config file (auto-loads if provided)
  - load_config(path)  # Alternative to config parameter
  - chat() / chat_async() → ChatGuideReply
  - add_user_message(message)
  - get_state() → dict with execution/progress/tasks/data
  - dump() → {variables, context, execution, audit}  # NEW: 4-layer export
  - get_progress() → {completed, total, percent, current_task}
  - get_current_task() → str
  - get_next_tasks(limit=3) → list[str]
  - get_next_blocks(limit=3) → list[list[str]]
  - is_waiting_for_user() → bool
  - is_finished() → bool
  - checkpoint(include_config=False) → dict
  - save_checkpoint(path, include_config=True)
  - load_checkpoint(path, api_key) → ChatGuide [classmethod]
  - from_checkpoint(checkpoint, api_key) → ChatGuide [classmethod]
  - set_session_id(session_id)
  - set_session_metadata(metadata)
  - add_stream_callback(callback)
  - get_metrics() → dict
  - reset_metrics()
  - get_prompt() → str
  - add_middleware(middleware_func)
  - add_task_hook(task_id, hook_func)
  # NEW: 4-layer architecture access
  - state → State (business variables)
  - context → Context (conversation history)
  - execution → ExecutionState (flow control)
  - audit → AuditLog (change tracking)

- State()  # Enhanced with Pythonic access
  - state.variable_name  # NEW: Pythonic access (recommended)
  - state.variable_name = value  # NEW: Pythonic setter
  - get(key, default=None)
  - set(key, value, source_task=None)  # NEW: source_task for audit
  - update(dict, source_task=None)
  - variables → dict  # NEW: Get all business data
  - resolve_template(template) → resolves {{var}} patterns
  - to_dict() → dict

- Context()  # NEW: Conversation history
  - history → list[Message]
  - session_id → str
  - metadata → dict
  - add_message(role, content)
  - get_history_dict() → list[dict]
  - to_dict() → dict

- ExecutionState()  # NEW: Flow control
  - status → str  # "idle" | "processing" | "awaiting_input" | "complete"
  - current_task → str
  - completed → list[str]
  - mark_complete(task_id)
  - is_completed(task_id) → bool
  - progress(total_tasks) → {completed, total, percent, current_task}
  - to_dict() → dict

- AuditLog()  # NEW: Change tracking
  - search(key=None, task=None, since=None) → list[dict]
  - get_latest(key) → dict
  - to_list() → list[dict]

- Plan(blocks: list[list[str]])
  - get_current_block() → Block
  - advance()
  - jump_to(index)
  - insert_block(index, tasks)
  - remove_block(index)
  - is_finished() → bool

- ChatGuideReply
  - text → str  # NEW: Alias for assistant_reply
  - assistant_reply → str
  - task_results → list[TaskResult]
  - tools → list[ToolCall]

- Plan(blocks: list[list[str]])
  - get_current_block() → list[str]
  - advance()
  - jump_to(index)
  - insert_block(index, tasks)
  - remove_block(index)
  - is_finished() → bool

Config YAML Structure:
state:
  key: value

plan:
  - [task1, task2]
  - [task3]

tasks:
  task_id:
    description: "What to do"
    expects: ["key1", "key2"]
    silent: false
    tools:
      - tool: tool_name
        args: {}

adjustments:
  - name: adjustment_name
    when: state.get("key") == value
    actions:
      - type: plan.insert_block / plan.jump_to / tone.set / state.set
        key: value

tone:
  - tone_name

tones:
  tone_name:
    description: "How to express"

State Structure from get_state():
{
  "execution": {status, current_block_index, current_tasks, is_finished, 
                pending_ui_tools, errors, error_count, retry_count},
  "progress": {completed_tasks, pending_tasks, total_tasks, completed_count, blocks},
  "tasks": {task_id: {status, description, expects, has_tools, is_silent}},
  "data": {extracted_key: value},
  "data_extractions": {key: {value, extracted_by, validated}},
  "data_coverage": {expected_keys, collected_keys, missing_keys, coverage_percent},
  "tone": [current_tones],
  "adjustments": {fired: [...], all: {...}},
  "conversation": {turn_count, user_message_count, last_user_message},
  "last_response": {task_results, tools_called, was_silent}
}

Streaming Events:
- {type: "task_complete", task_id, key, value}
- {type: "tool_call", tool, options}
- {type: "adjustment_fired", name, actions}
- {type: "error", error, context}
- {type: "llm_response", reply, was_silent}

Middleware Signature:
def middleware(context: dict) -> dict:
    # context has: state, plan, current_task, conversation_history, phase
    return modified_context

Task Hook Signature:
def hook(task_id: str, value: Any) -> None:
    # Called when task completes
```

---

**ChatGuide** - State-driven conversational agent framework
