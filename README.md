# ChatGuide Minimal v1

![ChatGuide](static/chatguide.png)

**Deterministic conversational AI framework with canonical configuration and mandatory extraction invariants.**

Build conversational AI that actually knows where it is in the conversation - with zero ambiguity in task completion and data extraction.

## Minimal v1 Benefits

- ✅ **Canonical Configuration**: Strict expects format eliminates ambiguity
- ✅ **Mandatory Extraction**: One result per expected key, null for missing data
- ✅ **Deterministic Completion**: Tasks complete when all expected keys have non-null values
- ✅ **Strict Key Whitelist**: Prevents state pollution from unexpected extractions
- ✅ **Automatic Re-ask**: Guarantees progress with up to 3 retries for incomplete extractions
- ✅ **Comprehensive Validation**: Config validation at startup with clear error messages
- ✅ **Debug Tools**: Session inspection and config hot-reloading for development

## Install

**Prerequisites:**
- Python 3.8+
- Gemini API key (get from [Google AI Studio](https://aistudio.google.com/))

**Environment Setup:**
```bash
# Clone and setup
git clone <repository-url>
cd chatguide

# Install Python dependencies
cd python && pip install -e .

# Set up environment variables
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

**Python Library:**
```bash
cd python && pip install -e .
```

**Web API (Full Stack):**
```bash
cd examples/fastapi_app
pip install fastapi uvicorn python-multipart
python main.py
# Access at http://localhost:8000
```

## Quick Start

**1. Define your flow in YAML (Canonical Format):**
```yaml
plan:
  - [greet]
  - [get_name, get_age]
  - [confirm]

tasks:
  greet:
    description: "Welcome the user warmly"
    expects: []  # No data extraction needed

  get_name:
    description: "Ask for the user's name"
    expects:
      - key: user_name
        type: string

  get_age:
    description: "Ask for age (1-120)"
    expects:
      - key: age
        type: number
        min: 1
        max: 120

  confirm:
    description: "Confirm the collected information"
    expects: []  # No data extraction needed
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

print(cg.data)  # {"user_name": "John"}
print(cg.get_progress())   # {"completed": 2, "total": 4, "percent": 50}
```

## Repository Structure

```
chatguide/
├── python/              # Python package
│   ├── chatguide/       # Main module (minimal v1)
│   └── scripts/         # Utility scripts
│       └── validate_config.py  # Config validator
├── configs/             # YAML configuration files
├── examples/            # Example applications
│   └── fastapi_app/     # FastAPI web API + React UI
│       ├── main.py      # FastAPI server
│       └── static/      # Web interface files
├── export_codebase.py   # Full codebase export utility
├── static/              # Project assets
└── README.md            # This file
```

## Core Concepts

### Plan
Ordered sequence of task blocks that execute sequentially:

```yaml
plan:
  - ["greet"]           # Block 0: executes first (sequential)
  - ["get_name", "get_age"]  # Block 1: executes after block 0 completes (parallel within block)
  - ["confirm"]         # Block 2: executes after block 1 completes
```

**Execution Rules:**
- **Blocks execute sequentially**: Block 1 waits for Block 0 to complete
- **Tasks within a block execute in parallel**: All tasks in a block run simultaneously
- **Single tasks should be in their own block**: Use `[["greet"]]` not `["greet"]`

### Tasks
LLM reasoning units that extract data with **canonical expects format**:

```yaml
tasks:
  get_name:
    description: "Ask for the user's name"
    expects:
      - key: user_name
        type: string
```

### Validation & Data Types
**Canonical Format Only**: All expects must be objects with `key` field. No string arrays allowed.

```yaml
# ✅ VALID - Canonical format
get_name:
  expects:
    - key: user_name
      type: string

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

# ❌ INVALID - These will be rejected at startup
expects: [user_name]           # String array not allowed
expects: ["user_name"]         # Still not allowed
```

### Core Invariants (Minimal v1)
- **Mandatory Extraction**: LLM must output exactly one `task_result` per expected key
- **Null Values**: Missing extractions get `value: null` automatically
- **Strict Whitelist**: Only expected keys accepted (prevents state pollution)
- **Deterministic Completion**: Task completes when all expected keys have non-null values
- **Re-ask Logic**: Automatically re-asks if extraction incomplete (up to 3 retries)

### Key Changes in Minimal v1
- **Configuration**: Strict canonical format eliminates ambiguity
- **Runtime**: Mandatory extraction prevents silent failures
- **Completion**: Deterministic rules (no "required" flags needed)
- **Safety**: Key whitelist prevents state pollution
- **Reliability**: Automatic re-ask guarantees progress

### Tones
Expression style (never affects logic):
```yaml
tones:
  professional: "Clear, courteous, efficient"
  empathetic: "Calm, warm, understanding"
```

## API Usage

ChatGuide provides both a Python library and a FastAPI web API for conversational AI applications.

### FastAPI Web API

**Start the server:**
```bash
cd examples/fastapi_app && pip install fastapi uvicorn python-multipart && python main.py
# Server runs on http://localhost:8000
```

**API Endpoints:**

#### POST `/api/chat`
Main chat endpoint for conversational interactions.

**Request Body:**
```json
{
  "message": "Hello, my name is Alice",
  "session_id": "optional-session-id",
  "action": "chat"
}
```

**Actions:**
- `"chat"` - Send a message (default)
- `"reset"` - Start a new conversation
- `"init"` - Initialize without sending a message

**Response:**
```json
{
  "reply": "Nice to meet you Alice! How old are you?",
  "session_id": "abc123-def456-...",
  "progress": {
    "completed": 2,
    "total": 4,
    "percent": 50,
    "current_task": "get_age"
  },
  "finished": false,
  "task_results": [
    {
      "task_id": "get_name",
      "key": "user_name",
      "value": "Alice"
    },
    {
      "task_id": "get_age",
      "key": "age",
      "value": null
    }
  ],
  "state_data": {
    "data": {"user_name": "Alice", "age": null},
    "messages": [...],
    "block": 1,
    "completed": ["get_name"],  // Only when all expected keys have non-null values
    "recent_keys": ["user_name", "age"]
  }
}
```

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "ChatGuide API"
}
```

#### GET `/api/debug/{session_id}`
Debug endpoint to inspect current session state (for development).

**Response:**
```json
{
  "session_id": "abc123",
  "finished": false,
  "current_block": 1,
  "total_blocks": 3,
  "progress": {...},
  "current_block_tasks": [...],
  "pending_tasks": [...],
  "completed_tasks": ["greet"],
  "extracted_data": {"user_name": "Alice"},
  "recent_keys": ["user_name"],
  "conversation_length": 3
}
```

#### POST `/api/reload-config`
Reload configuration for all active sessions (for development).

**Response:**
```json
{
  "status": "config_reloaded",
  "reloaded_sessions": 2,
  "failed_sessions": 0,
  "total_sessions": 2
}
```

#### GET `/api/progress/{session_id}`
Get detailed progress information for a session.

**Response:**
```json
{
  "session_id": "abc123",
  "finished": false,
  "overall_progress": {...},
  "block_progress": [...],
  "current_block_details": {...}
}
```

### Web Interface

Access the interactive chat interface at:
```
http://localhost:8000/static/index.html
```

Features:
- Real-time chat with progress visualization
- Task completion tracking with green highlighting
- Collected data display
- Session management

### Python Examples

**Basic Usage:**
```python
from chatguide import ChatGuide
import os

# Initialize
cg = ChatGuide(
    api_key=os.environ["GEMINI_API_KEY"],
    config="config.yaml"
)

# Start conversation
reply = cg.chat()
print(reply.text)  # "Hi! What's your name?"

# Continue conversation
cg.add_user_message("Alice")
reply = cg.chat()
print(reply.text)  # "Nice to meet you Alice! How old are you?"

# Check progress
print(cg.get_progress())  # {"completed": 2, "total": 4, "percent": 50}
print(cg.data)  # {"name": "Alice"}
```

**Advanced Features:**
```python
# Access conversation state
state = cg.state  # Full internal state
messages = cg.messages  # Conversation history
completed_tasks = list(cg.state["completed"])  # ["greet", "get_name"]

# Check if conversation is finished
if cg.is_finished():
    print("Conversation complete!")
```

## Configuration

**Config File Structure:**
Create `configs/config.yaml`:
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
    expects:
      - key: user_name
        type: string

  get_age:
    description: "Ask for age (1-120)"
    expects:
      - key: age
        type: number
        min: 1
        max: 120

  confirm:
    description: "Confirm the collected information"

tone: [friendly]

tones:
  friendly: {"description": "Warm, casual, and helpful"}
```

## Deployment

### Production Hosting

**Recommended Platforms:**
- **Railway + FastAPI**: Secure, Python-native, great for healthcare
- **Render + FastAPI**: Enterprise security, HIPAA-ready
- **Supabase + FastAPI**: Built-in auth, RLS security, audit logs
- **AWS Lambda + API Gateway**: Serverless deployment
- **Google Cloud Run**: Containerized deployment

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (for production)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
REDIS_URL=redis://localhost:6379  # For session storage
LOG_LEVEL=INFO
SESSION_TTL=3600  # Session timeout in seconds
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Considerations

**For Production Deployment:**

1. **API Key Management:**
   - Store `GEMINI_API_KEY` securely (never in code)
   - Use environment variables or secret management services
   - Rotate keys regularly

2. **CORS Configuration:**
   - Set specific `ALLOWED_ORIGINS` instead of `"*"`
   - Configure proper credentials handling

3. **Rate Limiting:**
   - Implement request throttling to prevent abuse
   - Consider API key authentication for external access

4. **Session Security:**
   - Use secure session IDs (UUID4 recommended)
   - Implement session expiration
   - Consider user authentication for sensitive applications

5. **Data Privacy:**
   - ChatGuide stores conversation data in memory by default
   - Implement proper data retention policies
   - Consider encryption for sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'chatguide'"**
   - Ensure you're in the correct directory: `cd python`
   - Install the package: `pip install -e .`
   - If using the FastAPI app, ensure you're running from the correct directory

2. **API Key Errors**
   - Verify `GEMINI_API_KEY` environment variable is set
   - API keys should start with "AIza" (Gemini API format)
   - Check API key has proper permissions for Gemini API

3. **Config File Not Found**
   - Ensure `configs/config.yaml` exists relative to your working directory
   - For FastAPI app, config should be at `../configs/config.yaml`
   - Check file permissions and path

4. **Configuration Validation Errors**
   - **"expects must be a dict object"**: Use `expects: [{"key": "name", "type": "string"}]` instead of `expects: ["name"]`
   - **"expects[0] must be a dict object"**: All expects entries must be objects with "key" field
   - **"task must have description"**: Every task needs a `description` field
   - **"tone reference not defined"**: Define tones in `tones` section before referencing in `tone` list

5. **Tasks Not Completing**
   - Check that `expects` format matches what the LLM is supposed to extract
   - Use simple string format for basic extraction: `expects: ["user_name"]`
   - Use object format for validation: `expects: [{"key": "age", "type": "number", "min": 1, "max": 120}]`
   - Tasks without `expects` complete automatically after execution

6. **Parallel vs Sequential Confusion**
   - Each array in `plan` represents a block of tasks
   - Tasks in the same block `["task1", "task2"]` run in parallel
   - Tasks in separate blocks run sequentially: block 0 completes before block 1 starts
   - Single tasks should be in their own block: `[["greet"], ["get_name"], ["confirm"]]`

7. **Session State Debugging**
   - Use `/api/debug/{session_id}` endpoint to inspect current state
   - Check current block, completed tasks, and extracted data
   - Verify task expectations match what was actually extracted

### Getting Help

- **Debug Endpoint**: Visit `http://localhost:8000/api/debug/{session_id}` for detailed session state
- **Config Validation**: Run your app to get immediate validation feedback at startup
- **Error Messages**: All errors now include specific details about what's wrong and how to fix it

### Testing Your Config

Use the built-in config validator:

```bash
# Validate config syntax and canonical format
python python/scripts/validate_config.py configs/config.yaml

# Test full ChatGuide initialization (requires GEMINI_API_KEY)
python python/scripts/validate_config.py configs/config.yaml --test-init
```

**Canonical Format Validation:**
- ✅ `expects: [{"key": "name", "type": "string"}]`
- ❌ `expects: ["name"]` - will be rejected
- ❌ `expects: [name]` - will be rejected

Or validate programmatically:

```python
from chatguide.utils.config_loader import load_config_file, validate_config

# Load and validate
data = load_config_file('configs/config.yaml')
errors = validate_config(data)

if errors:
    print("Config errors found:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Config is valid with canonical format!")
```

## License

MIT
