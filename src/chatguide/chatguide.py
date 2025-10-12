from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional, Literal, Set
from collections import defaultdict
import json, yaml, re, logging
from google import genai


# ---------- Schema ----------
class Task(BaseModel):
    """Task definition"""
    key: str
    description: str


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
        if self.current_state >= len(self.states):
            return False
        current_tasks = self.states[self.current_state]
        incomplete = [t for t in current_tasks if self.task_status.get(t) not in ["completed", "failed"]]
        if incomplete:
            print(f"⚠️ Cannot advance; still pending: {incomplete}")
            return False
        self.current_state += 1
        print(f"⏩ Advanced to state {self.current_state}")
        return True
    
    def is_finished(self) -> bool:
        return self.current_state >= len(self.states)


# ---------- Framework ----------
class ChatGuide:
    def __init__(self, debug: bool = False):
        # Core components
        self.guardrails: str = ""
        self.tasks: Dict[str, Task] = {}
        self.tones: Dict[str, str] = {}
        self.state_machine = StateMachine()
        self.debug: bool = debug
        
        # Setup logging
        if debug:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('chatguide.log', encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.conversation_log = open('conversation.log', 'w', encoding='utf-8')
        else:
            self.logger = None
            self.conversation_log = None

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

        # Track executed routes per update cycle to prevent duplicates
        self._executed_routes_this_cycle: Set[str] = set()
    
    def _debug_print(self, message: str):
        if self.debug and self.logger:
            self.logger.info(message)
    
    def _log_conversation(self, prompt: str, response: str):
        if self.debug and self.conversation_log:
            self.conversation_log.write(f"\n{'='*80}\nPROMPT:\n{prompt}\n")
            self.conversation_log.write(f"\n{'='*80}\nAI RESPONSE:\n{response}\n{'='*80}\n")
            self.conversation_log.flush()
    
    # ---------- Configuration ----------
    def add_task(self, key: str, description: str):
        task = Task(key=key, description=description)
        self.tasks[key] = task
        self._debug_print(f"📝 Added task: {key}")
    
    def load_from_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) if path.endswith((".yml", ".yaml")) else json.load(f)
        
        if "guardrails" in data:
            if isinstance(data["guardrails"], dict):
                guardrail_lines = [f"• {k.title()}: {v}" for k, v in data["guardrails"].items()]
                self.guardrails = "\n".join(guardrail_lines)
            else:
                self.guardrails = data["guardrails"]
        
        if "tasks" in data:
            for key, description in data["tasks"].items():
                self.add_task(key, description)
        
        if "tones" in data:
            self.tones = data["tones"]
        
        if "routes" in data:
            self.routes = data["routes"]
        
        self._debug_print(f"✅ Loaded configuration from {path}")
    
    def set_task_flow(self, batches: List[List[str]], persistent: List[str] = None):
        self.state_machine.set_flow(batches, persistent)
    
    def start_conversation(self, memory: str, starting_message: str, tones: List[str]):
        self.memory = memory
        self.chat_history = [f"{self.chatbot_name}: {starting_message}"]
        self.tones_active = tones
        self.turn_count = 0
    
    def set_chatbot_name(self, name: str):
        self.chatbot_name = name
        self._debug_print(f"🤖 Chatbot name set to: {name}")
    
    def set_user_name(self, name: str):
        self.user_name = name
        self._debug_print(f"👤 User name set to: {name}")
    
    # ---------- Validation ----------
    def validate_task_result(self, task_id: str, result: str) -> bool:
        return True
    
    # ---------- Prompt Building ----------
    def _build_task_description(self, task_id: str) -> str:
        if task_id not in self.tasks:
            return f"│ task_id: {task_id}\n│ description: [Task not defined]"
        task = self.tasks[task_id]
        return f"│ task_id: {task.key}\n│ description: {task.description}"
    
    def _build_prompt(self) -> str:
        current_tasks = self.state_machine.get_current_tasks()
        persistent_tasks = self.state_machine.get_persistent_tasks()
        
        next_state = self.state_machine.current_state + 1
        next_tasks = self.state_machine.states[next_state] if next_state < len(self.state_machine.states) else []
        
        current_desc = "\n".join([f"{t}: {self.tasks.get(t).description if t in self.tasks else 'Unknown'}" for t in current_tasks]) or "None"
        persistent_desc = "\n".join([f"{t}: {self.tasks.get(t).description if t in self.tasks else 'Unknown'}" for t in persistent_tasks]) or "None"
        next_desc = "\n".join([f"{t}: {self.tasks.get(t).description if t in self.tasks else 'Unknown'}" for t in next_tasks]) or "None"
        
        tone_instruction = " ".join([self.tones.get(t, t) for t in self.tones_active])
        dynamic_memory = self._build_memory()
        history = "\n".join(self.chat_history[-(self.max_history_turns * 2):])
        
        return f"""===============================================================================
                              CHATGUIDE PROMPT
===============================================================================

MEMORY:
{dynamic_memory}

CHAT HISTORY:
{history}

GUARDRAILS:
{self.guardrails}

CURRENT TASKS:
{current_desc}

PERSISTENT TASKS:
{persistent_desc}

NEXT TASKS:
{next_desc or "No next tasks"}

TONE: {tone_instruction}

OUTPUT FORMAT:
{{
  "tasks": [
    {{
      "task_id": "task_name",
      "result": "output_value"
    }}
  ],
  "persistent_tasks": [
    {{
      "task_id": "task_name",
      "result": "output_value"
    }}
  ],
  "assistant_reply": "your_response_here"
}}

RULES:
1. Once all CURRENT TASKS are completed, IMMEDIATELY advance to NEXT TASKS
2. Return empty string if task not completed


===============================================================================""".strip()
    
    def _build_memory(self) -> str:
        parts = [self.memory]
        if self.task_results:
            info_lines = []
            for task_id, result in self.task_results.items():
                if result and task_id not in ["detect_info_updates"]:
                    info_lines.append(f"• {task_id}: {result}")
            if info_lines:
                parts.append("Known info:\n" + "\n".join(info_lines))
        return "\n".join(parts)
    
    # ---------- Update ----------
    def update(self, model_output_json: str):
        """Process model output and update state"""
        self._debug_print("🔄 Processing model response...")
        self._executed_routes_this_cycle.clear()
        data = json.loads(model_output_json)

        # Process batch tasks
        batch_tasks = data.get("tasks", [])
        if batch_tasks:
            for task_result in batch_tasks:
                task_id = task_result["task_id"]
                result = task_result["result"].strip()
                current_tasks = self.state_machine.get_current_tasks()
                if task_id in current_tasks:
                    self.state_machine.increment_attempt(task_id)
                if result:
                    if self.validate_task_result(task_id, result):
                        self.task_results[task_id] = result
                        self.state_machine.mark_completed(task_id)
                        self._debug_print(f"✅ Task '{task_id}' completed: '{result}'")

        # Process persistent tasks
        persistent_tasks = data.get("persistent_tasks", [])
        if persistent_tasks:
            for task_result in persistent_tasks:
                task_id = task_result["task_id"]
                result = task_result["result"].strip()
                if result:
                    self.task_results[task_id] = result
                    if task_id == "detect_info_updates" and "update:" in result.lower():
                        self._handle_info_update(result)

        # Process routes
        self._process_routes()

        # Add to history
        assistant_reply = data.get("assistant_reply", "")
        self.chat_history.append(f"{self.chatbot_name}: {assistant_reply}")
        if len(self.chat_history) > self.max_history_turns * 2:
            self.chat_history = self.chat_history[-(self.max_history_turns * 2):]

        # --- FIXED ADVANCEMENT LOGIC ---
        self._debug_print("🔄 Checking state advancement...")
        if self.state_machine.current_state < len(self.state_machine.states):
            current_batch = self.state_machine.states[self.state_machine.current_state]
            incomplete = [t for t in current_batch if self.state_machine.task_status.get(t) not in ["completed", "failed"]]
            if not incomplete:
                advanced = self.state_machine.advance()
                if advanced:
                    self._debug_print(f"🚀 State advanced to {self.state_machine.current_state}")
            else:
                self._debug_print(f"⏸️ Still waiting on: {incomplete}")
        # --------------------------------

        self._debug_print("✅ Update complete!")
    
    def _handle_info_update(self, update_result: str):
        if "=" in update_result:
            parts = update_result.split("=", 1)
            if len(parts) == 2:
                task_part = parts[0].strip().lower().replace("update:", "").strip()
                new_value = parts[1].strip()
                for task_id in list(self.task_results.keys()):
                    if task_id in task_part or task_id.replace("_", " ") in task_part:
                        old_value = self.task_results.get(task_id, "NOT_SET")
                        if old_value != new_value:
                            self.task_results[task_id] = new_value
                            if task_id in self.state_machine.task_status:
                                self.state_machine.task_status[task_id] = "pending"
                            self._process_routes()
                        break
    
    def _process_routes(self):
        for i, route in enumerate(self.routes):
            condition = route.get("condition", "")
            route_id = f"route_{i}_{condition}"
            if route_id in self._executed_routes_this_cycle:
                continue
            if self._evaluate_condition(condition):
                self._execute_route(route)
                self._executed_routes_this_cycle.add(route_id)
                break
    
    def _evaluate_condition(self, condition: str) -> bool:
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
        action = route.get("action")
        if action == "change_tone":
            self.tones_active = route.get("tones", [])
        elif action == "add_persistent_task":
            task_id = route.get("task_id")
            if task_id and task_id not in self.state_machine.persistent_tasks:
                self.state_machine.persistent_tasks.append(task_id)
                self.state_machine.task_status[task_id] = "active"
        elif action == "set_user_name":
            task_id = route.get("task_id", "get_name")
            if task_id in self.task_results and self.task_results[task_id]:
                self.set_user_name(self.task_results[task_id])
    
    # ---------- Chat ----------
    def add_user_message(self, message: str):
        self.chat_history.append(f"{self.user_name}: {message}")
    
    def chat(self, model="gemini/gemini-2.5-flash-lite", api_key=None, temperature=0.6, max_tokens=256):
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
        
        self._log_conversation(prompt, reply_obj.model_dump_json())
        self.update(reply_obj.model_dump_json())
        return reply_obj
    
    # ---------- Utility ----------
    def prompt(self) -> str:
        return self._build_prompt()
    
    def get_debug_info(self) -> dict:
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
