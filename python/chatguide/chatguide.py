"""ChatGuide - lean conversational agent framework."""

from typing import Dict, Any, Optional, Union, List
from .schemas import ChatGuideReply, ExpectDefinition, TaskResult
from .core.task import Task
from .builders.prompt import PromptBuilder, PromptView
from .io.llm import run_llm
from .utils.config_loader import load_config_file, validate_config, normalize_expects
from .utils.response_parser import parse_llm_response


class ChatGuide:
    """State-driven conversational agent."""
    
    def __init__(self, api_key: str = None, config: Any = None, debug: bool = False):
        self.api_key = api_key
        self.debug = debug
        self.config_path = config if isinstance(config, str) else None  # Store path for reloading

        # === SINGLE SOURCE OF TRUTH ===
        # Everything dynamic lives in state
        self.state = {
            "data": {},           # Extracted key-value data
            "messages": [],       # Conversation history
            "block": 0,           # Current block index
            "completed": set(),   # Completed task IDs
            "recent_keys": [],    # Recent keys in order of extraction/correction
            "last_error": None,   # Store validation errors here
        }

        # === STATIC CONFIG (loaded once) ===
        self.config = {
            "tasks": {},          # task_id -> {description, expects, silent}
            "blocks": [],         # [[task_ids], [task_ids], ...]
            "tone": "",
            "guardrails": "",
            "language": "en",
        }

        if config:
            self._load_config(config)

    def reload_config(self) -> bool:
        """Reload configuration from the original path. Returns True if successful."""
        if not self.config_path:
            return False

        try:
            # Store current state to preserve conversation
            current_state = self.state.copy()

            # Reload config
            self._load_config(self.config_path)

            # Restore state (but reset block progression to avoid inconsistencies)
            self.state = current_state

            if self.debug:
                print(f"[DEBUG] Config reloaded from {self.config_path}")
            return True
        except Exception as e:
            if self.debug:
                print(f"[ERROR] Config reload failed: {e}")
            return False

    # =========== CONFIG ===========
    
    def _load_config(self, config: Union[str, Dict]):
        """Load configuration with validation."""
        data = config if isinstance(config, dict) else load_config_file(config)

        # Validate config
        errors = validate_config(data)
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {err}" for err in errors)
            raise ValueError(error_msg)

        # Blocks (plan)
        self.config["blocks"] = data.get("plan", [])

        # Tasks
        for task_id, task_def in data.get("tasks", {}).items():
            expects = task_def.get("expects", [])
            # Normalize expects using the new function
            normalized = normalize_expects(expects)

            self.config["tasks"][task_id] = {
                "description": task_def.get("description", ""),
                "expects": normalized,
                "silent": task_def.get("silent", False),
            }
        
        # Tone
        tone_ids = data.get("tone", [])
        tone_defs = data.get("tones", {})
        if tone_ids:
            self.config["tone"] = " ".join(
                tone_defs.get(t, {}).get("description", t) if isinstance(tone_defs.get(t), dict) else t
                for t in tone_ids
            )
        
        # Guardrails & language
        guardrails = data.get("guardrails", [])
        self.config["guardrails"] = "\n".join(guardrails) if isinstance(guardrails, list) else guardrails
        self.config["language"] = data.get("language", "en")
        
        # Initial state data
        if "state" in data:
            self.state["data"].update(data["state"])
    
    # =========== CHAT ===========
    
    def chat(self, model: str = "gemini/gemini-2.0-flash-exp", api_key: str = None, max_retries: int = 2) -> ChatGuideReply:
        """Execute one chat turn. Re-asks if task not complete due to null values."""
        retry_count = 0
        while retry_count < max_retries:
            task = self._current_task()
            is_silent = task and task.get("silent", False)

            if self.debug:
                block_idx = self.state["block"]
                current_block_tasks = self._current_block_tasks()
                pending_in_block = [tid for tid in current_block_tasks if tid not in self.state["completed"]]
                current_task_id = self._current_task_id()
                if current_task_id:
                    is_complete = self._task_is_complete(current_task_id)
                    print(f"[DEBUG] Block {block_idx}: {len(pending_in_block)} pending tasks {pending_in_block}, current task: {current_task_id}, complete: {is_complete}")
                else:
                    print(f"[DEBUG] Block {block_idx}: {len(pending_in_block)} pending tasks {pending_in_block}, no current task")

            # Build prompt and call LLM
            prompt = self._build_prompt()
            reply = self._call_llm(prompt, model, api_key or self.api_key)

            # Update state
            self._process_reply(reply)

            # Check if current task is complete
            current_task_id = self._current_task_id()
            if current_task_id and not self._task_is_complete(current_task_id):
                # Task not complete due to null values - re-ask by continuing the loop
                retry_count += 1
                if retry_count < max_retries:
                    if self.debug:
                        null_keys = [exp.key for exp in task.get("expects", []) if self.state["data"].get(exp.key) is None]
                        print(f"[DEBUG] Task '{current_task_id}' incomplete due to null values for keys: {null_keys}. Re-asking... ({retry_count}/{max_retries})")
                    continue
                else:
                    # Max retries reached - force completion with current data (may include nulls)
                    if self.debug:
                        print(f"[DEBUG] Max retries ({max_retries}) reached for task '{current_task_id}', force-completing with available data")
                    self.state["completed"].add(current_task_id)

                    # Advance if block complete
                    if self._block_complete():
                        if self.debug:
                            print(f"[DEBUG] Block {self.state['block']} complete, advancing to block {self.state['block'] + 1}")
                        self.state["block"] += 1

            # Silent tasks loop, visible tasks return
            if not is_silent:
                self.state["messages"].append({"role": "assistant", "content": reply.assistant_reply})
                return reply
    
    def add_user_message(self, message: str):
        """Add user message."""
        self.state["messages"].append({"role": "user", "content": message})
    
    # =========== STATE HELPERS ===========
    
    @property
    def data(self) -> Dict:
        """Shortcut to extracted data."""
        return self.state["data"]
    
    @property
    def messages(self) -> List:
        """Shortcut to conversation history."""
        return self.state["messages"]
    
    def _current_task(self) -> Optional[Dict]:
        """Get current task definition."""
        task_id = self._current_task_id()
        return self.config["tasks"].get(task_id) if task_id else None
    
    def _current_task_id(self) -> Optional[str]:
        """Get current task ID."""
        blocks = self.config["blocks"]
        idx = self.state["block"]
        if idx >= len(blocks):
            return None
        for task_id in blocks[idx]:
            if task_id not in self.state["completed"]:
                return task_id
        return None
    
    def is_finished(self) -> bool:
        """Check if all blocks complete."""
        return self.state["block"] >= len(self.config["blocks"])
    
    def get_progress(self) -> Dict:
        """Get progress info."""
        total = sum(len(b) for b in self.config["blocks"])
        completed = len(self.state["completed"])
        return {
            "completed": completed,
            "total": total,
            "percent": int(completed / total * 100) if total else 100,
            "current_task": self._current_task_id(),
        }
    
    # =========== INTERNAL ===========
    
    def _build_prompt(self) -> str:
        """Build LLM prompt."""
        # Current task
        current_task = self._make_task(self._current_task_id())
        
        # Pending tasks in current block
        pending = [self._make_task(tid) for tid in self._current_block_tasks() 
                   if tid not in self.state["completed"]]
        
        # Next block's first task (for smooth transitions)
        next_block_task = None
        next_idx = self.state["block"] + 1
        if next_idx < len(self.config["blocks"]) and self.config["blocks"][next_idx]:
            next_block_task = self._make_task(self.config["blocks"][next_idx][0])
        
        # Get recent extractions from state
        recent_extractions = [
            {"key": k, "value": self.state["data"][k]}
            for k in self.state["recent_keys"][-10:]  # Last 10 recent keys
        ]

        view = PromptView(
            current_task=current_task,
            pending_tasks=pending,
            completed_tasks=list(self.state["completed"]),
            state=self.state["data"],
            tone_text=self.config["tone"] or "Natural and helpful",
            guardrails=self.config["guardrails"],
            history=self.state["messages"],
            language=self.config["language"],
            next_block_task=next_block_task,
            recent_extractions=recent_extractions,
        )
        # Inject the error into the view manually or add a field
        view.last_error = self.state.get("last_error")

        return PromptBuilder(view).build()
    
    def _make_task(self, task_id: str) -> Optional[Task]:
        """Create Task object from config."""
        if not task_id:
            return None
        tdef = self.config["tasks"].get(task_id, {})
        return Task(
            id=task_id,
            description=tdef.get("description", ""),
            expects=tdef.get("expects", []),
            silent=tdef.get("silent", False),
        )
    
    def _call_llm(self, prompt: str, model: str, api_key: str) -> ChatGuideReply:
        """Call LLM."""
        try:
            result = run_llm(
                prompt, model=model, api_key=api_key,
                extra_config={"response_schema": ChatGuideReply.model_json_schema()}
            )
            return parse_llm_response(result.content)
        except Exception as e:
            if self.debug:
                print(f"[ERROR] {e}")
            return ChatGuideReply(assistant_reply=f"Error: {e}", task_results=[], tools=[])
    
    def _process_reply(self, reply: ChatGuideReply):
        """Process reply: update state, complete tasks, advance."""
        self.state["last_error"] = None  # Reset error at start of processing

        current_task_id = self._current_task_id()
        if not current_task_id:
            return

        current_task_def = self.config["tasks"].get(current_task_id, {})
        expected_keys = [exp.key for exp in current_task_def.get("expects", [])]

        # 1. STRICT KEY WHITELIST: Only accept keys listed in current task's expects
        filtered_results = []
        for tr in reply.task_results:
            if tr.key in expected_keys:
                filtered_results.append(tr)
            elif self.debug:
                print(f"[WARNING] Rejected unexpected key '{tr.key}' from task results (not in expects)")

        # 2. MANDATORY EXTRACTION ENTRIES: Ensure one result per expected key
        # Create TaskResult objects for missing keys with value=None
        result_dict = {tr.key: tr for tr in filtered_results}
        complete_results = []

        for expected_key in expected_keys:
            if expected_key in result_dict:
                complete_results.append(result_dict[expected_key])
            else:
                # Missing key - create with null value
                complete_results.append(TaskResult(
                    task_id=current_task_id,
                    key=expected_key,
                    value=None
                ))
                if self.debug:
                    print(f"[DEBUG] Added missing result for key '{expected_key}' with null value")

        # 3. VALIDATION & UPDATE (REPLACE YOUR STEP 3 WITH THIS)
        for tr in complete_results:
            # Skip validation if value is already None
            if tr.value is None:
                continue

            # Find the expectation definition for this key
            expects = current_task_def.get("expects", [])

            # Perform validation
            is_valid = True
            error_msg = ""

            # Find the specific ExpectDefinition for this key
            matching_exp = next((e for e in expects if e.key == tr.key), None)

            if matching_exp:
                # Use the validate_value method from ExpectDefinition
                is_valid, error_msg = matching_exp.validate_value(tr.value)

            if is_valid:
                self.state["data"][tr.key] = tr.value
                if tr.key not in self.state["recent_keys"]:
                    self.state["recent_keys"].append(tr.key)
            else:
                # VALIDATION FAILED
                if self.debug:
                    print(f"[VALIDATION FAIL] Key: {tr.key}, Value: {tr.value}, Error: {error_msg}")

                # 1. Don't save the data (keep it None/old)
                # 2. Set the error so the Prompt knows to complain
                self.state["last_error"] = f"User provided '{tr.value}' for '{tr.key}', but that is invalid: {error_msg}. Ask them to correct it."

                # If one fails, we stop processing results to ensure we ask about this one
                # (Optional: you could collect all errors)
                break

        # 4. Check if current task is complete (all non-null)
        if self._task_is_complete(current_task_id):
            self.state["completed"].add(current_task_id)
            if self.debug:
                print(f"[DEBUG] Completed task '{current_task_id}' (all expected keys have non-null values)")

            # 5. Advance if block complete
            if self._block_complete():
                if self.debug:
                    print(f"[DEBUG] Block {self.state['block']} complete, advancing to block {self.state['block'] + 1}")
                self.state["block"] += 1

    def _task_is_complete(self, task_id: str) -> bool:
        """Check if task is complete: all expected keys have non-null values."""
        task_def = self.config["tasks"].get(task_id, {})
        expected_keys = [exp.key for exp in task_def.get("expects", [])]
        return all(self.state["data"].get(key) is not None for key in expected_keys)

    def _validate_runtime_state(self):
        """Validate runtime state for consistency."""
        errors = []

        # Check that all completed tasks actually exist
        for task_id in self.state["completed"]:
            if task_id not in self.config["tasks"]:
                errors.append(f"Completed task '{task_id}' not found in config")

        # Check that extracted data matches task expectations
        for task_id in self.state["completed"]:
            task_def = self.config["tasks"].get(task_id, {})
            expects = task_def.get("expects", [])

            # If task has expects, check that at least one key was extracted
            if expects:
                extracted_any = False
                for exp in expects:
                    exp_key = exp.key if hasattr(exp, 'key') else exp
                    if exp_key in self.state["data"]:
                        extracted_any = True
                        break

                if not extracted_any and self.debug:
                    print(f"[WARNING] Task '{task_id}' completed but no expected keys found in data")

        if errors and self.debug:
            print(f"[WARNING] Runtime validation errors: {errors}")
    
    def _current_block_tasks(self) -> List[str]:
        """Get task IDs in current block."""
        blocks = self.config["blocks"]
        idx = self.state["block"]
        return blocks[idx] if idx < len(blocks) else []
    
    def _block_complete(self) -> bool:
        """Check if current block is complete."""
        return all(tid in self.state["completed"] for tid in self._current_block_tasks())
    
    def _find_task_for_key(self, key: str) -> Optional[str]:
        """Find task that expects this key."""
        for task_id in self._current_block_tasks():
            task_def = self.config["tasks"].get(task_id, {})
            for exp in task_def.get("expects", []):
                exp_key = exp.key if hasattr(exp, "key") else exp
                if exp_key == key:
                    return task_id
        return None
