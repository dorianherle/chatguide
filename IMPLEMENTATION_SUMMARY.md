# ChatGuide Architecture - Implementation Complete ✅

## What Was Built

A complete refactor implementing the new state-driven conversational agent framework.

### Core Architecture

```
State       → Flat dictionary with {{template}} resolution
Plan        → Ordered task blocks with manipulation
Tasks       → LLM reasoning units
Tools       → Async execution (UI, API, functions)
Adjustments → Reactive rules watching state
Tone        → Expression style layer
```

### Files Structure

```
src/chatguide/
├── state.py              # Flat state + template resolver
├── plan.py               # Plan manipulation
├── adjustments.py        # Reactive rules engine
├── tool_executor.py      # Unified async tool execution
├── schemas.py            # Pydantic models (simplified)
├── chatguide.py          # Main orchestrator
└── builders/
    └── prompt.py         # Prompt generation

app.py                    # Streamlit UI with adjustment tracking
realistic_hotel_config.yaml  # Example config (new format)
```

### Deleted Old Code

- ✅ `core/containers/` (flow, tasks, conversation, etc.)
- ✅ `routing/` (evaluator, executor)
- ✅ `demo_realistic_hotel.py`
- ✅ Old `config.py`

## Key Features Implemented

### 1. Flat State with Templates
```python
state.set("user_name", "John")
template = "Hello {{user_name}}"
resolved = state.resolve_template(template)  # "Hello John"
```

### 2. Plan Manipulation
```python
plan = Plan([[task1, task2], [task3]])
plan.jump_to(2)
plan.insert_block(1, [new_task])
plan.remove_block(0)
```

### 3. Adjustments (Reactive Rules)
```yaml
adjustments:
  - name: recognize_returning
    when: state.get("user_name") is not None
    actions:
      - type: tone.set
        tones: ["returning_guest"]
      - type: state.set
        key: is_returning_guest
        value: true
```

### 4. Simplified Task Results
Each task outputs ONE key-value pair:
```json
{
  "task_id": "get_reservation_name",
  "key": "user_name",
  "value": "John Smith"
}
```

### 5. Tool Integration
- UI tools (button_choice, card_swipe)
- Async execution
- State updates from tool outputs

## UI Features

### Streamlit App (`app.py`)

**Shows:**
- 💬 Conversation flow
- 📊 Live state monitoring
- 🎯 Current plan block
- 🎨 Active tone
- ⚡ **Fired adjustments** (NEW!)
- 🛠️ Interactive tools (buttons, animations)

**Adjustments Display:**
```
⚡ Adjustment fired: route_to_checkin
⚡ Adjustment fired: recognize_returning
```

## Working Examples

### Hotel Check-in Flow

1. **Initial**: Welcome + button choice
2. **Select "Check In"** → `route_to_checkin` adjustment fires → Plan jumps to block 1
3. **Provide name** → `recognize_returning` adjustment fires → Tone changes to "returning_guest"
4. **Process payment** → Card swipe animation shown → Room assigned

### State Evolution
```python
# Start
{'user_name': None, 'purpose': None, ...}

# After "Check In"
{'user_name': None, 'purpose': 'Check In', ...}

# After providing name
{'user_name': 'John Smith', 'is_returning_guest': True, ...}
```

### Tone Changes
```
professional → returning_guest → completing_payment
```

## Test Files

- `test_working.py` - Full flow test with LLM
- `simple_chat.py` - Terminal chatbot
- `app.py` - Streamlit UI (run with `streamlit run app.py`)

## Configuration Format

```yaml
state:
  user_name: null

plan:
  - [task1, task2]
  - [task3]

tasks:
  task1:
    description: "Do something"
    expects: ["user_name"]
    tools:
      - tool: tool_id
        args:
          param: "{{user_name}}"

tools:
  tool_id:
    type: ui
    description: "Tool description"

adjustments:
  - name: adjustment_name
    when: state.get("key") == "value"
    actions:
      - type: plan.jump_to
        index: 1

tones:
  tone_name:
    description: "How to speak"

tone:
  - professional
```

## Runtime Loop

```python
for block in plan:
    for task in block:
        # 1. LLM reasoning
        reply = llm(task_description, state)
        state.update(reply.task_results)
        
        # 2. Execute tools
        for tool in task.tools:
            args = resolve_templates(tool.args, state)
            output = await execute_tool(tool, args)
            state.update(output)
        
        # 3. Evaluate adjustments
        fired = adjustments.evaluate(state, plan, tone)
        
        # Track and display fired adjustments
        display_adjustments(fired)
```

## Success Metrics ✅

- ✅ Config loads correctly
- ✅ Prompts build with state
- ✅ LLM calls work with structured output
- ✅ State updates from task results
- ✅ Plan manipulation works
- ✅ Adjustments fire and modify plan/tone/state
- ✅ Template resolution works
- ✅ Tools execute (UI tools rendered)
- ✅ **Adjustments tracked and displayed in UI**
- ✅ **Card swipe animation shows during payment**
- ✅ **Tone changes visible in real-time**

## Quick Start

```bash
# Install
pip install -e .

# Set API key
echo "GEMINI_API_KEY=your_key" > .env

# Run Streamlit app
streamlit run app.py

# Or terminal chat
python simple_chat.py
```

## Architecture Principles ✅

1. **State is single source of truth** ✅
2. **Tasks are LLM-driven** ✅
3. **Tools are runtime-driven** ✅
4. **Args resolved from state via {{var}}** ✅
5. **Tools write back to state** ✅
6. **Multi-tool tasks allowed** ✅
7. **Adjustments control reactivity** ✅
8. **Tone never affects logic** ✅

---

**Status:** Implementation Complete
**Date:** 2025-10-19
**Architecture:** Clean, simple, extensible

