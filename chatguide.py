from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional, Literal
from collections import defaultdict
import json, yaml, re
from google import genai


# ---------- Schema ----------
class TaskOutput(BaseModel):
    """Defines what a task should output"""
    type: Literal["string", "enum", "regex"]
    validation: Optional[str] = None  # enum values or regex pattern
    allow_empty: bool = False  # Can task return empty string


class Task(BaseModel):
    """Task definition with output specification"""
    key: str
    description: str
    output: TaskOutput
    max_attempts: int = 5


class TaskResult(BaseModel):
    task_id: str
    result: str


class ChatGuideReply(BaseModel):
    tasks: List[TaskResult]
    persistent_tasks: List[TaskResult] = []
    assistant_reply: str


# ---------- State Machine ----------
class StateMachine:
    """Explicit state machine for task flow"""
    
    def __init__(self):
        self.states: List[List[str]] = []  # Batches of task keys
        self.persistent_tasks: List[str] = []
        self.current_state: int = 0
        self.task_status: Dict[str, str] = {}  # "pending", "completed", "failed"
        self.task_attempts: Dict[str, int] = defaultdict(int)
    
    def set_flow(self, batches: List[List[str]], persistent: List[str] = None):
        self.states = batches
        self.persistent_tasks = persistent or []
        self.current_state = 0
        
        # Initialize all tasks as pending
        for batch in batches:
            for task in batch:
                self.task_status[task] = "pending"
        for task in self.persistent_tasks:
            self.task_status[task] = "active"
    
    def get_current_tasks(self) -> List[str]:
        """Get incomplete tasks from current batch"""
        if self.current_state >= len(self.states):
            return []
        return [t for t in self.states[self.current_state] 
                if self.task_status.get(t) != "completed"]
    
    def get_persistent_tasks(self) -> List[str]:
        """Get active persistent tasks"""
        return [t for t in self.persistent_tasks 
                if self.task_status.get(t) == "active"]
    
    def mark_completed(self, task_id: str):
        """Mark a task as completed"""
        if task_id not in self.persistent_tasks:
            self.task_status[task_id] = "completed"
    
    def mark_failed(self, task_id: str):
        """Mark a task as failed after max attempts"""
        self.task_status[task_id] = "failed"
        print(f"❌ Task '{task_id}' failed after max attempts")
    
    def increment_attempt(self, task_id: str):
        """Increment attempt counter for a task"""
        self.task_attempts[task_id] += 1
    
    def get_attempts(self, task_id: str) -> int:
        return self.task_attempts[task_id]
    
    def advance(self):
        """Try to advance to next state if current batch complete"""
        current_tasks = self.states[self.current_state] if self.current_state < len(self.states) else []
        
        # Check if all tasks in current batch are completed or failed
        all_done = all(self.task_status.get(t) in ["completed", "failed"] 
                      for t in current_tasks)
        
        if all_done and self.current_state < len(self.states):
            self.current_state += 1
            print(f"⏩ Advanced to state {self.current_state}")
            return True
        return False
    
    def is_finished(self) -> bool:
        return self.current_state >= len(self.states)


# ---------- Framework ----------
class ChatGuideV2:
    def __init__(self):
        # Core components
        self.guardrails: str = ""
        self.tasks: Dict[str, Task] = {}
        self.tones: Dict[str, str] = {}
        self.state_machine = StateMachine()
        
        # Conversation state
        self.memory: str = ""
        self.chat_history: List[str] = []
        self.max_history_turns: int = 10
        self.tones_active: List[str] = ["neutral"]
        self.turn_count: int = 0
        
        # Task results
        self.task_results: Dict[str, str] = {}
        
        # Routes
        self.routes: List[Dict[str, Any]] = []
        
        # Participant names
        self.chatbot_name: str = "Assistant"
        self.user_name: str = "Human"
    
    # ---------- Configuration ----------
    def add_task(self, key: str, description: str, output_spec: Dict[str, Any], max_attempts: int = 5):
        """Add a task with output specification"""
        task = Task(
            key=key,
            description=description,
            output=TaskOutput(**output_spec),
            max_attempts=max_attempts
        )
        self.tasks[key] = task
    
    def load_from_file(self, path: str):
        """Load configuration from YAML/JSON"""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) if path.endswith((".yml", ".yaml")) else json.load(f)
        
        # Load guardrails
        if "guardrails" in data:
            self.guardrails = data["guardrails"]
        
        # Load tasks with output specs
        if "tasks" in data:
            for key, task_data in data["tasks"].items():
                if isinstance(task_data, str):
                    # Legacy format - just description
                    self.add_task(key, task_data, {"type": "string", "allow_empty": False})
                else:
                    # New format with output spec
                    self.add_task(
                        key, 
                        task_data["description"],
                        task_data["output"],
                        task_data.get("max_attempts", 5)
                    )
        
        # Load tones
        if "tones" in data:
            self.tones = data["tones"]
        
        # Load routes
        if "routes" in data:
            self.routes = data["routes"]
        
        print(f"✅ Loaded configuration from {path}")
    
    def set_task_flow(self, batches: List[List[str]], persistent: List[str] = None):
        """Set up the state machine flow"""
        self.state_machine.set_flow(batches, persistent)
    
    def start_conversation(self, memory: str, starting_message: str, tones: List[str]):
        """Initialize conversation"""
        self.memory = memory
        self.chat_history = [f"{self.chatbot_name}: {starting_message}"]
        self.tones_active = tones
        self.turn_count = 0
    
    def set_chatbot_name(self, name: str):
        """Set the chatbot's name for personalized conversation"""
        self.chatbot_name = name
        print(f"🤖 Chatbot name set to: {name}")
    
    def set_user_name(self, name: str):
        """Set the user's name for personalized conversation"""
        self.user_name = name
        print(f"👤 User name set to: {name}")
    
    # ---------- Validation ----------
    def validate_task_result(self, task_id: str, result: str) -> bool:
        """Validate task result against output specification"""
        if task_id not in self.tasks:
            return True  # Unknown task, accept
        
        task = self.tasks[task_id]
        output_spec = task.output
        
        # Check if empty is allowed
        if not result.strip():
            return output_spec.allow_empty
        
        # Type-specific validation
        if output_spec.type == "enum":
            if not output_spec.validation:
                return True
            valid_values = [v.strip() for v in output_spec.validation.split(",")]
            return result.strip() in valid_values
        
        elif output_spec.type == "regex":
            if not output_spec.validation:
                return True
            return bool(re.match(output_spec.validation, result.strip()))
        
        elif output_spec.type == "string":
            return True  # Any string is valid
        
        return True
    
    # ---------- Prompt Building ----------
    def _build_task_description(self, task_id: str) -> str:
        """Build task description with output specification"""
        if task_id not in self.tasks:
            return f"{task_id}: [Task not defined]"
        
        task = self.tasks[task_id]
        desc = f"{task.key}: {task.description}"
        
        # Add output specification
        output = task.output
        if output.type == "enum":
            desc += f" | OUTPUT: one of [{output.validation}]"
        elif output.type == "regex":
            desc += f" | OUTPUT: must match pattern {output.validation}"
        elif not output.allow_empty:
            desc += f" | OUTPUT: non-empty string"
        
        # Add attempt info
        attempts = self.state_machine.get_attempts(task_id)
        if attempts > 0:
            desc += f" (attempt {attempts + 1}/{task.max_attempts})"
        
        return desc
    
    def _build_prompt(self) -> str:
        """Build the system prompt"""
        current_tasks = self.state_machine.get_current_tasks()
        persistent_tasks = self.state_machine.get_persistent_tasks()
        
        # Get next batch preview
        next_state = self.state_machine.current_state + 1
        next_tasks = []
        if next_state < len(self.state_machine.states):
            next_tasks = self.state_machine.states[next_state]
        
        current_desc = "\n".join([f"- {self._build_task_description(t)}" for t in current_tasks]) or "None"
        persistent_desc = "\n".join([f"- {self._build_task_description(t)}" for t in persistent_tasks]) or "None"
        next_desc = "\n".join([f"- {t}: {self.tasks.get(t).description if t in self.tasks else 'Unknown'}" for t in next_tasks]) or "None"
        
        tone_instruction = " ".join([self.tones.get(t, t) for t in self.tones_active])
        
        # Build memory with collected info
        dynamic_memory = self._build_memory()
        
        # Build history
        history = "\n".join(self.chat_history[-(self.max_history_turns * 2):])
        
        return f"""
#MEMORY:
{dynamic_memory}

#RECENT CHAT HISTORY:
{history}

#GUARDRAILS:
{self.guardrails}

#TASKS

##CURRENT BATCH TASKS:
{current_desc}

##PERSISTENT TASKS - ALWAYS ACTIVE:
{persistent_desc}

##NEXT BATCH (for smooth transitions):
{next_desc}

#TONE:
{tone_instruction}

#OUTPUT FORMAT (STRICT JSON):
{{
  "tasks": [
    {{
      "task_id": "<task_id>",
      "result": "<result_matching_output_spec>"
    }}
  ],
  "persistent_tasks": [
    {{
      "task_id": "<task_id>",
      "result": "<result>"
    }}
  ],
  "assistant_reply": "<your_reply>"
}}

#RULES:
1. NEVER repeat yourself
2. Work on CURRENT BATCH tasks first
3. When you complete ALL current batch tasks, IMMEDIATELY flow into the first NEXT BATCH task in your reply - make the transition seamless
4. Each task specifies OUTPUT requirements - follow them exactly
5. Empty result = task not completed yet
6. Keep conversation natural and flowing - smooth transitions between tasks
7. Extract information from user responses accurately
""".strip()
    
    def _build_memory(self) -> str:
        """Build memory with collected information"""
        parts = [self.memory]
        
        if self.task_results:
            info_lines = []
            for task_id, result in self.task_results.items():
                if result and task_id != "detect_info_updates":
                    label = task_id.replace("_", " ").title()
                    info_lines.append(f"{label}: {result}")
            
            if info_lines:
                parts.append("\nKnown information:\n" + "\n".join(info_lines))
        
        return "\n".join(parts)
    
    # ---------- Update ----------
    def update(self, model_output_json: str):
        """Process model output and update state"""
        data = json.loads(model_output_json)
        
        # Process batch tasks - allow tasks from current AND next batch
        for task_result in data.get("tasks", []):
            task_id = task_result["task_id"]
            result = task_result["result"].strip()
            
            # Only increment attempts for current batch tasks
            current_tasks = self.state_machine.get_current_tasks()
            if task_id in current_tasks:
                self.state_machine.increment_attempt(task_id)
            
            if result:
                # Validate result
                if self.validate_task_result(task_id, result):
                    self.task_results[task_id] = result
                    self.state_machine.mark_completed(task_id)
                    print(f"✅ Task '{task_id}' completed: {result}")
                else:
                    print(f"⚠️ Task '{task_id}' validation failed: {result}")
                    
                    # Check if max attempts reached (only for current batch)
                    if task_id in current_tasks:
                        task = self.tasks.get(task_id)
                        if task and self.state_machine.get_attempts(task_id) >= task.max_attempts:
                            self.state_machine.mark_failed(task_id)
        
        # Process persistent tasks
        for task_result in data.get("persistent_tasks", []):
            task_id = task_result["task_id"]
            result = task_result["result"].strip()
            
            if result and self.validate_task_result(task_id, result):
                self.task_results[task_id] = result
                print(f"🔄 Persistent task '{task_id}': {result}")
                
                # Handle info updates
                if task_id == "detect_info_updates" and "update:" in result.lower():
                    self._handle_info_update(result)
        
        # Add to history
        assistant_reply = data.get("assistant_reply", "")
        self.chat_history.append(f"{self.chatbot_name}: {assistant_reply}")
        
        # Trim history
        if len(self.chat_history) > self.max_history_turns * 2:
            self.chat_history = self.chat_history[-(self.max_history_turns * 2):]
        
        # Try to advance state
        self.state_machine.advance()
        
        # Process routes
        self._process_routes()
    
    def _handle_info_update(self, update_result: str):
        """Handle information updates detected by detect_info_updates task"""
        # Expected format: "update: task_id = new_value"
        if "=" in update_result:
            parts = update_result.split("=", 1)
            if len(parts) == 2:
                task_part = parts[0].strip().lower().replace("update:", "").strip()
                new_value = parts[1].strip()
                
                # Extract task_id from the update string
                for task_id in list(self.task_results.keys()):
                    if task_id in task_part or task_id.replace("_", " ") in task_part:
                        print(f"📝 Updating {task_id}: '{self.task_results.get(task_id)}' → '{new_value}'")
                        self.task_results[task_id] = new_value
                        # Mark the task as not completed so it needs revalidation
                        if task_id in self.state_machine.task_status:
                            self.state_machine.task_status[task_id] = "pending"
                        
                        # Re-process routes since task results changed
                        # (e.g., if name changed, update user_name)
                        self._process_routes()
                        break
    
    def _process_routes(self):
        """Process route conditions and actions"""
        for route in self.routes:
            if self._evaluate_condition(route.get("condition", "")):
                self._execute_route(route)
                break
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Safely evaluate route condition"""
        if not condition:
            return False
        
        try:
            context = {
                "__builtins__": {},
                "task_results": self.task_results,
                "turn_count": self.turn_count,
                "state": self.state_machine.current_state,
                "task_turn_counts": dict(self.state_machine.task_attempts),
                "current_tasks": self.state_machine.get_current_tasks(),
                "len": len,
                "max": max,
                "min": min,
            }
            return eval(condition, context)
        except:
            return False
    
    def _execute_route(self, route: dict):
        """Execute route action"""
        action = route.get("action")
        
        if action == "change_tone":
            self.tones_active = route.get("tones", [])
            print(f"🔄 Changed tone to {self.tones_active}")
        
        elif action == "add_persistent_task":
            task_id = route.get("task_id")
            if task_id and task_id not in self.state_machine.persistent_tasks:
                self.state_machine.persistent_tasks.append(task_id)
                self.state_machine.task_status[task_id] = "active"
                print(f"➕ Added persistent task: {task_id}")
        
        elif action == "set_user_name":
            # Set user name from a task result
            task_id = route.get("task_id", "get_name")
            if task_id in self.task_results and self.task_results[task_id]:
                self.set_user_name(self.task_results[task_id])
    
    # ---------- Chat ----------
    def add_user_message(self, message: str):
        """Add user message to history"""
        self.chat_history.append(f"{self.user_name}: {message}")
    
    def chat(self, model="gemini/gemini-2.5-flash-lite", api_key=None, temperature=0.6, max_tokens=256):
        """Generate AI response"""
        provider, model_name = model.split("/", 1)
        prompt = self._build_prompt()
        self.turn_count += 1
        
        if provider != "gemini":
            raise NotImplementedError("Only Gemini provider supported")
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ChatGuideReply.model_json_schema(),
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        
        # Parse response
        raw = getattr(response, "parsed", None) or getattr(response, "text", None)
        if raw is None:
            raise ValueError("Gemini returned no content")
        
        if isinstance(raw, ChatGuideReply):
            reply_obj = raw
        elif isinstance(raw, dict):
            reply_obj = ChatGuideReply.model_validate(raw)
        elif isinstance(raw, str):
            reply_obj = ChatGuideReply.model_validate(json.loads(raw))
        else:
            raise ValueError(f"Unexpected response type: {type(raw)}")
        
        # Update state
        self.update(reply_obj.model_dump_json())
        return reply_obj
    
    # ---------- Utility ----------
    def prompt(self) -> str:
        """Get current prompt for debugging"""
        return self._build_prompt()
    
    def get_debug_info(self) -> dict:
        """Get current state information"""
        return {
            "turn_count": self.turn_count,
            "state": self.state_machine.current_state,
            "current_tasks": self.state_machine.get_current_tasks(),
            "persistent_tasks": self.state_machine.get_persistent_tasks(),
            "task_results": self.task_results.copy(),
            "task_status": dict(self.state_machine.task_status),
            "task_attempts": dict(self.state_machine.task_attempts),
            "is_finished": self.state_machine.is_finished(),
        }

