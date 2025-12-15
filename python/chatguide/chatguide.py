"""ChatGuide - lean conversational agent framework."""

from typing import Dict, Any, Optional, Union, List
from .schemas import ChatGuideReply, ExpectDefinition
from .core.task import Task
from .builders.prompt import PromptBuilder, PromptView
from .io.llm import run_llm
from .utils.config_loader import load_config_file
from .utils.response_parser import parse_llm_response


class ChatGuide:
    """State-driven conversational agent."""
    
    def __init__(self, api_key: str = None, config: Any = None, debug: bool = False):
        self.api_key = api_key
        self.debug = debug
        
        # === SINGLE SOURCE OF TRUTH ===
        # Everything dynamic lives in state
        self.state = {
            "data": {},           # Extracted key-value data
            "messages": [],       # Conversation history
            "block": 0,           # Current block index
            "completed": set(),   # Completed task IDs
            "recent_keys": [],    # Recent keys in order of extraction/correction
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
    
    # =========== CONFIG ===========
    
    def _load_config(self, config: Union[str, Dict]):
        """Load configuration."""
        data = config if isinstance(config, dict) else load_config_file(config)
        
        # Blocks (plan)
        self.config["blocks"] = data.get("plan", [])
        
        # Tasks
        for task_id, task_def in data.get("tasks", {}).items():
            expects = task_def.get("expects", [])
            # Normalize expects to have .key attribute
            normalized = []
            for e in expects:
                if isinstance(e, str):
                    normalized.append(ExpectDefinition(key=e))
                elif isinstance(e, dict):
                    normalized.append(ExpectDefinition(**e))
                else:
                    normalized.append(e)
            
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
    
    def chat(self, model: str = "gemini/gemini-2.0-flash-exp", api_key: str = None) -> ChatGuideReply:
        """Execute one chat turn. Auto-continues through silent tasks."""
        while True:
            task = self._current_task()
            is_silent = task and task.get("silent", False)
            
            # Build prompt and call LLM
            prompt = self._build_prompt()
            reply = self._call_llm(prompt, model, api_key or self.api_key)
            
            # Update state
            self._process_reply(reply)
            
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
        # 1. Update data and track recent keys
        for tr in reply.task_results:
            self.state["data"][tr.key] = tr.value
            if tr.key not in self.state["recent_keys"]:
                self.state["recent_keys"].append(tr.key)
        
        # 2. Complete tasks
        for tr in reply.task_results:
            task_id = tr.task_id or self._find_task_for_key(tr.key)
            if task_id:
                self.state["completed"].add(task_id)
        
        # Auto-complete tasks with no expects
        for task_id in self._current_block_tasks():
            if task_id not in self.state["completed"]:
                task_def = self.config["tasks"].get(task_id, {})
                if not task_def.get("expects"):
                    self.state["completed"].add(task_id)
        
        # 3. Advance if block complete
        if self._block_complete():
            self.state["block"] += 1
    
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
