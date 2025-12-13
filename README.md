# ChatGuide

![ChatGuide](python/chatguide/static/chatguide.png)

Build conversational AI that actually knows where it is in the conversation.

## Install

**Python:**
```bash
cd python && pip install -e .
```

## Quick Start

**1. Define your flow in YAML:**
```yaml
plan:
  - [greet]
  - [get_name, get_age]
  - [confirm]

tasks:
  greet:
    description: "Welcome the user warmly"
  
  get_name:
    description: "Ask for the user's name"
    expects: [user_name]
  
  get_age:
    description: "Ask for age (1-120)"
    expects:
      - key: age
        type: number
        min: 1
        max: 120
  
  confirm:
    description: "Confirm the collected information"
```

**2. Run it:**

```python
from chatguide import ChatGuide
import os

cg = ChatGuide(
    api_key=os.environ["GEMINI_API_KEY"],
    config="config.yaml"
)

reply = cg.chat()
print(reply.text)  # "Hi! What's your name?"

cg.add_user_message("John")
reply = cg.chat()
print(reply.text)  # "Nice to meet you John! How old are you?"

print(cg.state.user_name)  # "John"
print(cg.get_progress())   # {"completed": 2, "total": 4, "percent": 50}
```

## Repository Structure

```
chatguide/
├── python/           # Python package
│   └── chatguide/    # Main module
├── configs/          # Shared YAML configs
├── tests/            # Test suite
└── examples/         # Example applications
    ├── fastapi_app/  # FastAPI web server
    └── streamlit_demo.py  # Streamlit UI
```

## Core Concepts

### Plan
Ordered sequence of task blocks:
```yaml
plan:
  - [greet]           # Block 0: single task
  - [get_name, get_age]  # Block 1: parallel tasks
  - [confirm]         # Block 2
```

### Tasks
LLM reasoning units that extract data:
```yaml
tasks:
  get_name:
    description: "Ask for the user's name"
    expects: [user_name]  # Saves to state.user_name
```

### Validation
For numbers and enums:
```yaml
get_age:
  expects:
    - key: age
      type: number
      min: 1
      max: 120

get_mood:
  expects:
    - key: mood
      type: enum
      choices: [happy, sad, neutral]
```

### Tones
Expression style (never affects logic):
```yaml
tones:
  professional: "Clear, courteous, efficient"
  empathetic: "Calm, warm, understanding"
```

## Examples

```bash
# Run Streamlit demo
cd examples && streamlit run streamlit_demo.py

# Run FastAPI server
cd examples/fastapi_app && pip install -r requirements.txt && python main.py
# Then open: http://localhost:8000/static/index.html
```

## Deployment

**Recommended for Psychology Apps:**
- **Railway + FastAPI**: Secure, Python-native, great for healthcare
- **Render + FastAPI**: Enterprise security, HIPAA-ready
- **Supabase + FastAPI**: Built-in auth, RLS security, audit logs

**For Prototyping:**
- **Streamlit Cloud**: Quick demos (not for production psychology apps)

## License

MIT
