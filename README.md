# ChatGuide

![ChatGuide](static/chatguide.png)

**State-driven conversational agent framework**

A clean, declarative framework for building guided conversational AI where the LLM performs reasoning, the runtime executes tools, and reactive adjustments keep everything dynamic.

```
┌─────────┐
│  State  │ ← Central memory (flat dict)
└────┬────┘
     │
┌────▼────┐    ┌──────────┐    ┌─────────────┐
│  Plan   │───▶│  Tasks   │───▶│    Tools    │
└─────────┘    └──────────┘    └─────────────┘
     ▲              │                   │
     │              ▼                   ▼
┌────┴────────┐  ┌─────────────────────┴─┐
│ Adjustments │  │   Update State        │
└─────────────┘  └───────────────────────┘
```

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Set API Key

```bash
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=your_key_here
```

### 3. Run Demo

```bash
streamlit run app.py
```

Or test in terminal:
```bash
python test_recognize_adjustment.py
```

## Core Concepts

### State
Flat dictionary storing all variables:
```python
state.set("user_name", "John")
state.get("user_name")  # "John"
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
LLM reasoning units that extract data:
```yaml
tasks:
  collect_name:
    description: "Ask for the user's name and extract it"
    expects: ["user_name"]
    silent: false  # Show AI response (default)
```

**Silent tasks** collect data without showing a reply:
```yaml
extract_name:
  description: "Extract user_name from their message"
  expects: ["user_name"]
  silent: true  # No reply shown, immediate next task
```

Each task outputs one key-value pair:
```json
{
  "task_id": "collect_name",
  "key": "user_name",
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

# Initialize
cg = ChatGuide(api_key="your_key")
cg.load_config("config.yaml")

# Chat
reply = cg.chat()
print(reply.assistant_reply)

# Add user message
cg.add_user_message("My name is John")
reply = cg.chat()

# Check state
print(cg.state.to_dict())  # {'user_name': 'John', ...}
print(cg.tone)             # ['excited']
```

## Architecture Principles

1. **State is single source of truth** - Everything flows through it
2. **Tasks are LLM-driven** - Reasoning, language, decisions
3. **Tools are runtime-driven** - Deterministic actions
4. **Args resolved from state** - `{{var}}` templates
5. **Tools write to state** - Automatic state updates
6. **Multi-tool tasks allowed** - Sequential execution
7. **Adjustments control reactivity** - Watch state, modify plan/tone
8. **Tone never affects logic** - Purely expressive

## Project Structure

```
chatguide/
├── src/chatguide/
│   ├── state.py              # Flat state + templates
│   ├── plan.py               # Plan manipulation
│   ├── adjustments.py        # Reactive rules
│   ├── tool_executor.py      # Tool execution
│   ├── schemas.py            # Pydantic models
│   ├── chatguide.py          # Main orchestrator
│   ├── builders/
│   │   └── prompt.py         # Prompt generation
│   ├── io/
│   │   └── llm.py            # LLM providers
│   └── utils/
│       └── config_loader.py  # YAML parsing
│
├── app.py                    # Streamlit demo
├── realistic_hotel_config.yaml
└── test_recognize_adjustment.py
```

## Testing

```bash
# Test adjustment system
python test_recognize_adjustment.py

# Test full flow
python test_working.py

# Run Streamlit app
streamlit run app.py
```

## Advanced Features

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
5. **Test incrementally** - Use test files to verify behavior

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

See `realistic_hotel_config.yaml` for a complete hotel receptionist example featuring:
- Multi-path conversation (check-in, check-out, inquiries)
- Silent tasks for name extraction
- Returning guest recognition
- Tone changes based on state
- UI tools (button choices, card swipe animation)

## License

MIT

---

**Built with simplicity in mind** - Clean architecture, minimal abstractions, maximum clarity.
