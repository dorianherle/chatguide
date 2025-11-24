# ChatGuide Python

Original Python implementation of ChatGuide.

## Installation

```bash
pip install -r requirements.txt
```

Or install as package:

```bash
pip install -e .
```

## Usage

```python
from chatguide import ChatGuide
import os

guide = ChatGuide(
    api_key=os.environ["GEMINI_API_KEY"],
    config="configs/config.yaml"
)

# Start conversation
reply = guide.chat()
print(reply.assistant_reply)

# User responds
guide.add_user_message("I'm John")
reply = guide.chat()
print(reply.assistant_reply)

# Check progress
print(guide.get_progress())
```

## Structure

- `src/chatguide/` - Main package
- `examples/` - Example configurations and demos
- `tests/` - Test suite

See main README.md for full documentation.

