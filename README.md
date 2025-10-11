# ChatGuide Framework

A Python framework for building structured, task-driven conversational AI using Google's Gemini models.

## 🏗️ Core Building Blocks

### 1. Tasks
Specific objectives the AI should accomplish. Defined as:
```python
tasks = {
    "get_name": "Ask for or identify the user's name.",
    "get_emotion": "Classify the user's emotion as one of: happy, sad, angry, anxious, neutral."
}
```

### 2. Tones
Conversational style and personality:
```python
tones = {
    "neutral": "Be clear, factual, and balanced.",
    "empathetic": "Be calm, warm, and understanding.",
    "playful": "Be witty, use light humor, and keep it casual."
}
```

### 3. Task Flow
Tasks execute in batches sequentially:
```python
task_flow = [
    ["get_name", "get_origin"],    # Batch 1: Execute simultaneously
    ["get_location"],              # Batch 2: Execute after batch 1
    ["get_emotion", "reflect"]    # Batch 3: Execute after batch 2
]
```

### 4. Routes
Routes enable conditional conversation flow by changing:
- **Current tasks**: Add or switch tasks in current batch
- **Tones**: Change conversational style
- **Batch flow**: Jump to different task batches

Routes are processed automatically after each AI response.

## 🔧 Basic Usage

```python
from chatguide import ChatGuide
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize and configure
guide = ChatGuide()
guide.load_from_file("config.yaml")
guide.set_task_flow([
    ["get_name", "get_origin"],
    ["get_location"],
    ["get_emotion", "reflect", "suggest"]
])

# Start conversation
guide.start_conversation(
    memory="We're running a friendly onboarding chat.",
    starting_message="Hi there!",
    tones=["neutral"]
)

# Chat loop
while not guide.all_done():
    user_input = input("👤 You: ")
    guide.chat_history += f"\nUser: {user_input}"
    
    reply = guide.chat(model="gemini/gemini-2.5-flash-lite", api_key=GEMINI_API_KEY)
    print("🤖 Assistant:", reply.assistant_reply)
```

## 📋 Configuration File (config.yaml)

```yaml
tasks:
  get_name: "Ask for or identify the user's name."
  get_origin: "Find out where the user is from."
  get_location: "Find out where the user currently lives."
  get_emotion: "Classify the user's emotion as one of: happy, sad, angry, anxious, neutral."
  reflect: "Acknowledge and mirror the user's feeling gently."
  suggest: "Offer a supportive or relevant suggestion."

tones:
  neutral: "Be clear, factual, and balanced."
  empathetic: "Be calm, warm, and understanding."
  playful: "Be witty, use light humor, and keep it casual."
  professional: "Be concise, polite, and formal."
  encouraging: "Use supportive and positive phrasing."
  curious: "Ask thoughtful questions and show genuine interest."
  assertive: "Be confident and direct — encourage the user to answer clearly."
  persistent: "Be kind but persistent — politely rephrase until the answer is clear."

routes:
  - condition: "completed_tasks.get('get_origin') == True"
    action: "add_tasks"
    tasks: ["offer_language"]
```

## 🔄 API Reference

### Core Methods
- `load_from_file(path)`: Load configuration from YAML/JSON
- `set_task_flow(task_batches)`: Define task execution order
- `start_conversation(memory, starting_message, tones)`: Initialize conversation
- `chat(model, api_key)`: Generate AI response
- `all_done()`: Check if all tasks completed

### State Properties
- `completed_tasks`: Dict of completed task status
- `current_batch_idx`: Current task batch index
- `tones_active`: Currently active tones
- `chat_history`: Full conversation history
- `memory`: Conversation context

### Response Schema
```python
class ChatGuideReply(BaseModel):
    tasks: List[TaskResult]
    assistant_reply: str

class TaskResult(BaseModel):
    task_id: str
    result: str
    completed: bool
```

## 🔄 Route Implementation

Routes are automatically processed after each AI response. They enable dynamic conversation flow based on conditions.

### Route Structure
```yaml
routes:
  - condition: "max([task_turn_counts.get(task, 0) for task in current_tasks]) > 2"
    action: "change_tone"
    tones: ["persistent"]
  
  - condition: "completed_tasks.get('get_emotion') == 'sad'"
    action: "change_tone"
    tones: ["empathetic"]
  
  - condition: "turn_count > 10"
    action: "switch_tasks"
    tasks: ["summarize", "next_steps"]
```

### Available Actions
- **`add_tasks`**: Add tasks to current batch
- **`switch_tasks`**: Replace current batch with new tasks
- **`change_tone`**: Change active conversational tones
- **`jump_batch`**: Jump to a specific task batch

### Condition Variables
- `completed_tasks`: Dict of completed task status
- `turn_count`: Number of conversation turns
- `task_turn_counts`: Dict of turns per task
- `current_tasks`: Currently active incomplete tasks (completed tasks are filtered out)
- `next_tasks`: Next batch of tasks
- `tones_active`: Currently active tones
- `memory`: Conversation context
- `chat_history`: Full conversation history

## 📦 Installation

```bash
pip install -r requirements.txt
```

Required dependencies:
- `google-genai`
- `pydantic`
- `python-dotenv`
- `pyyaml`

## 🔍 Debugging

```python
# Print current state
print("Current tasks:", guide.get_current_tasks())
print("Completed tasks:", guide.completed_tasks)
print("Active tones:", guide.tones_active)
print("Turn count:", guide.turn_count)

# Print full prompt
print(guide.prompt())
```

## 🎯 Example: Persistent Tone Routing

The example configuration demonstrates routing in action:

1. **Initial tone**: `["neutral"]`
2. **Route condition**: After 2 turns with incomplete tasks
3. **Route action**: Change tone to `["persistent"]`
4. **Result**: AI becomes more persistent in getting answers

This shows how routes can dynamically modify conversation behavior based on user engagement.