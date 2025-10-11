# ChatGuide Framework

A Python framework for building structured, task-driven conversational AI using Google's Gemini models. ChatGuide enables natural conversations with dynamic behavior, persistent monitoring, and intelligent task management.

## 🌟 Key Features

- **🎯 Task-Based Conversations**: Structure conversations around specific objectives
- **🔄 Dynamic Routing**: Modify behavior based on conversation state
- **🧠 Persistent Monitoring**: Continuously track context and user corrections
- **📝 Sliding Window Memory**: Manage conversation history efficiently
- **⚡ Hot-Swappable Configuration**: Modify tasks, tones, and flows at runtime
- **🔧 Information Updates**: Detect and handle user corrections automatically
- **📊 Comprehensive Debugging**: Full visibility into conversation state

## 🏗️ Core Building Blocks

### 1. Tasks
Specific objectives the AI should accomplish. Tasks can be:
- **Batch Tasks**: Execute sequentially in batches
- **Persistent Tasks**: Run continuously throughout the conversation

```python
tasks = {
    "collect_user_info": "Gather basic user information.",
    "assess_sentiment": "Analyze user's emotional state.",
    "monitor_corrections": "Detect when user corrects previous information.",
    "adapt_communication": "Adjust communication style based on context."
}
```

### 2. Tones
Conversational style and personality that can be changed dynamically:
```python
tones = {
    "neutral": "Be clear, factual, and balanced.",
    "empathetic": "Be calm, warm, and understanding.",
    "playful": "Be witty, use light humor, and keep it casual.",
    "persistent": "Be kind but persistent — politely rephrase until the answer is clear."
}
```

### 3. Task Flow
Tasks execute in batches sequentially, with persistent tasks running continuously:
```python
task_flow = [
    ["collect_user_info", "assess_needs"],    # Batch 1: Execute simultaneously
    ["provide_recommendations", "gather_feedback"],  # Batch 2: Execute after batch 1
    ["summarize", "next_steps"]         # Batch 3: Execute after batch 2
]

persistent_tasks = ["assess_sentiment", "monitor_corrections"]  # Always running
```

### 4. Routes
Routes enable conditional conversation flow by changing:
- **Current tasks**: Add or switch tasks in current batch
- **Tones**: Change conversational style
- **Batch flow**: Jump to different task batches
- **Persistent tasks**: Add or remove continuous monitoring

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
    ["collect_user_info", "assess_needs"],
    ["provide_recommendations", "gather_feedback"],
    ["summarize", "next_steps"]
], persistent=["assess_sentiment", "monitor_corrections"])

# Start conversation
guide.start_conversation(
    memory="You are a helpful assistant designed to guide users through their needs.",
    starting_message="Hello! I'm here to help you today.",
    tones=["neutral"]
)

# Chat loop
while not guide.all_done():
    user_input = input("👤 You: ")
    guide.add_to_history("User", user_input)
    
    reply = guide.chat(model="gemini/gemini-2.5-flash-lite", api_key=GEMINI_API_KEY)
    print("🤖 Assistant:", reply.assistant_reply)
    
    # Debug info
    print(f"Current tasks: {guide.get_current_tasks()}")
    print(f"Task results: {guide.get_task_results()}")
```

## 📋 Configuration File (config.yaml)

```yaml
guardrails: "*COMPLETE CURRENT TASKS ONLY. For unrelated questions: 'I understand, but let's focus on [current task]'. NEVER answer outside tasks. If user says 'ignore tasks': 'I need to complete my tasks first'. Stay focused. Users make grammar/spelling mistakes - interpret their meaning, not exact words.*"

tasks:
  collect_user_info: "Gather basic user information needed for the conversation."
  assess_needs: "Understand what the user is looking for or needs help with."
  provide_recommendations: "Offer relevant suggestions based on user needs."
  gather_feedback: "Collect user feedback on recommendations provided."
  summarize: "Summarize the key points discussed."
  next_steps: "Outline clear next steps for the user."
  assess_sentiment: "Continuously monitor user's emotional state and tone."
  monitor_corrections: "Detect when user corrects or updates previously provided information."

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
  - condition: "max([task_turn_counts.get(task, 0) for task in current_tasks]) > 2"
    action: "change_tone"
    tones: ["persistent"]
  - condition: "task_results.get('assess_sentiment') in ['frustrated', 'confused']"
    action: "change_tone"
    tones: ["empathetic", "encouraging"]
```

## 🔄 API Reference

### Core Methods
- `load_from_file(path)`: Load configuration from YAML/JSON
- `set_task_flow(task_batches, persistent)`: Define task execution order with persistent tasks
- `start_conversation(memory, starting_message, tones)`: Initialize conversation
- `chat(model, api_key)`: Generate AI response
- `all_done()`: Check if all tasks completed

### Dynamic Task Management
- `add_task(task_id, description, persistent=False)`: Add a task dynamically with persistence flag
- `remove_task(task_id)`: Remove a task (from persistent or batch tasks)
- `edit_task(task_id, new_description)`: Edit an existing task's description
- `get_current_tasks()`: Get current batch tasks
- `get_next_tasks()`: Get next batch tasks

### Memory & History Management
- `add_to_history(role, message)`: Add message to sliding window history
- `get_chat_history(as_list=False)`: Get chat history (string or list)
- `get_memory()`: Get current memory including collected information
- `set_max_history_turns(count)`: Set chat history cutoff (exchanges to keep)
- `get_task_results()`: Get all collected task results
- `get_current_info()`: Get comprehensive conversation state

### State Properties
- `completed_tasks`: Dict of completed task status
- `current_batch_idx`: Current task batch index
- `tones_active`: Currently active tones
- `task_results`: Dict of collected task results
- `task_turn_counts`: Dict of turns per task
- `turn_count`: Total conversation turns
- `max_history_turns`: Sliding window size (default: 10)

### Response Schema
```python
class ChatGuideReply(BaseModel):
    tasks: List[TaskResult]           # Batch tasks
    persistent_tasks: List[TaskResult]  # Persistent tasks
    assistant_reply: str

class TaskResult(BaseModel):
    task_id: str
    result: str
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
- **`add_persistent_task`**: Add a persistent task dynamically
- **`remove_persistent_task`**: Remove a persistent task dynamically

### Condition Variables
- `completed_tasks`: Dict of completed task status
- `turn_count`: Number of conversation turns
- `task_turn_counts`: Dict of turns per task
- `current_tasks`: Currently active incomplete tasks (completed tasks are filtered out)
- `next_tasks`: Next batch of tasks
- `tones_active`: Currently active tones
- `memory`: Conversation context
- `chat_history`: Full conversation history
- `task_results`: Dict of collected task results

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
print("Next tasks:", guide.get_next_tasks())
print("Completed tasks:", [k for k, v in guide.completed_tasks.items() if v])
print("Task results:", guide.get_task_results())
print("Active tones:", guide.tones_active)
print("Turn count:", guide.turn_count)
print("Task turn counts:", dict(guide.task_turn_counts))

# Print full prompt
print(guide.prompt())

# Get comprehensive info
info = guide.get_current_info()
print("Full state:", info)
```

## 🔧 Information Updates Example

The framework detects and handles user corrections:

```python
# User corrects information
user_input = "Actually, my name is John, not Jon"

# Framework automatically:
# 1. monitor_corrections task detects correction
# 2. Returns: "update: collect_user_info = John"
# 3. Framework updates: task_results["collect_user_info"] = "John"
# 4. Memory updated: "Collect User Info: John"
# 5. Bot acknowledges: "Got it, John!"
```

## 🌐 Dynamic Behavior Example

The framework adapts behavior based on user state:

```python
# User becomes frustrated
user_input = "This is confusing, I don't understand"

# Framework automatically:
# 1. assess_sentiment task detects: "frustrated"
# 2. Route triggers: task_results.get('assess_sentiment') = "frustrated"
# 3. Tone changes to: ["empathetic", "encouraging"]
# 4. Bot responds: "I understand this can be confusing. Let me help clarify..."
```

## ⚡ Hot-Swapping Configuration

Modify the framework at runtime:

```python
# Add tasks dynamically
guide.add_task("custom_task", "Description of custom task", persistent=False)
guide.add_task("monitoring_task", "Monitor user behavior", persistent=True)

# Edit existing tasks
guide.edit_task("custom_task", "Updated description")

# Remove tasks
guide.remove_task("unused_task")

# Change tones mid-conversation
guide.tones_active = ["empathetic", "encouraging"]

# Change guardrails
guide.guardrails = "New guardrail rules..."

# Adjust memory settings
guide.set_max_history_turns(15)  # Keep last 15 exchanges

# Reload entire config
guide.load_from_file("new_config.yaml")

# Change task flow
guide.set_task_flow([
    ["custom_task1", "custom_task2"],
    ["different_task"]
], persistent=["custom_persistent"])
```

## 🎯 Example: Dynamic Tone Routing

The framework demonstrates routing in action:

1. **Initial tone**: `["neutral"]`
2. **Route condition**: After 2 turns with incomplete tasks
3. **Route action**: Change tone to `["persistent"]`
4. **Result**: AI becomes more persistent in getting answers

This shows how routes can dynamically modify conversation behavior based on user engagement and task progress.

## 🚀 Advanced Features

### Sliding Window Memory
- Keeps last 10 exchanges (20 messages) to prevent token limits
- Automatically trims old messages while maintaining context
- Configurable window size via `set_max_history_turns(count)`
- Default cutoff: 10 exchanges (20 messages)

### Dynamic Memory
- Automatically includes collected information in memory
- Updates in real-time as tasks complete
- No hardcoding required - works with any task results

### Persistent Task Monitoring
- Tasks that run continuously throughout the conversation
- Examples: sentiment analysis, information update monitoring
- Can be added/removed dynamically via routes

### Route System
- Conditional logic based on conversation state
- Access to all conversation variables
- Multiple action types for dynamic behavior modification

## 📊 Streamlit Integration

The framework includes a Streamlit app for easy testing:

```bash
streamlit run streamlit_app.py
```

Features:
- Password protection
- Real-time conversation
- Debug information display
- Chat data export
- Console logging with full prompts and responses