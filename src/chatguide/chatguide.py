"""ChatGuide - main orchestrator."""

import logging
from typing import List, Set, Optional, Dict, Any

from .core.state import ConversationState
from .core.config import Config
from .builders.prompt import PromptBuilder
from .routing.evaluator import RouteEvaluator
from .routing.executor import RouteExecutor
from .io.llm import run_llm
from .utils.config_loader import load_config_file, parse_guardrails, parse_tasks, parse_tones, parse_routes
from .utils.response_parser import parse_llm_response
from .utils.debug_formatter import DebugFormatter, ResponseFormatter
from .schemas import ChatGuideReply, Task


class ChatGuide:
    """Lightweight orchestrator for guided conversations."""
    
    def __init__(self, debug: bool = False, api_key: str = None):
        # Core components
        self.state = ConversationState(debug=debug)
        self.config = Config()
        self.routes: List[Dict[str, Any]] = []
        
        # Settings
        self.debug = debug
        self.api_key = api_key
        
        # Internal
        self._executed_routes: Set[str] = set()
        self._route_executor = RouteExecutor(self)
        
        # Logging
        if debug:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(message)s",
                handlers=[
                    logging.FileHandler("chatguide.log", encoding="utf-8"),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
            self.conversation_log = open("conversation.log", "w", encoding="utf-8")
        else:
            self.logger = None
            self.conversation_log = None

    # ==================================================================
    # Configuration
    # ==================================================================
    def load_config(self, path: str):
        """Load configuration from file."""
        data = load_config_file(path)
        
        self.config.guardrails = parse_guardrails(data)
        self.config.tones = parse_tones(data)
        self.routes = parse_routes(data)
        
        for key, desc in parse_tasks(data).items():
            self.config.add_task(key, desc)
        
        self._log(f"Loaded config from {path}")
    
    def set_flow(self, batches: List[List[str]], persistent: List[str] = None):
        """Set task flow."""
        self.state.flow.set_flow(batches, persistent)
        
        # Initialize task statuses via direct access
        for batch in batches:
            for task in batch:
                self.state.tracker.status[task] = "pending"
        for task in (persistent or []):
            self.state.tracker.status[task] = "active"
    
    # ==================================================================
    # Conversation
    # ==================================================================
    def start(self, memory: str, tones: List[str]):
        """Start conversation.
        
        Note: No first_message needed! Add an initial task batch like:
            ["introduce_yourself"]
        and let the LLM generate the intro dynamically.
        """
        self.state.conversation.memory = memory
        self.state.interaction.tones = tones
        self.state.interaction.turn_count = 0
    
    def add_user_message(self, message: str):
        """Add user message to history."""
        self.state.conversation.add_message(self.state.participants.user, message)
    
    def chat(
        self,
        model: str = "gemini/gemini-2.5-flash-lite",
        api_key: str = None,
        temperature: float = 0.6,
        max_tokens: int = 256
    ) -> ChatGuideReply:
        """Execute one chat turn."""
        # Build prompt
        prompt = PromptBuilder(self.config, self.state).build()
        self.state.interaction.turn_count += 1
        
        # Call LLM
        key = api_key or self.api_key
        raw = run_llm(prompt, model=model, api_key=key, temperature=temperature,
                      max_tokens=max_tokens,
                      extra_config={"response_schema": ChatGuideReply.model_json_schema()})
        
        # Parse and process
        reply = parse_llm_response(raw)
        self._process_reply(reply)
        
        # Log
        if self.debug and self.conversation_log:
            self.conversation_log.write(f"\n{'='*80}\nPROMPT:\n{prompt}\n")
            self.conversation_log.write(f"\nRESPONSE:\n{reply.model_dump_json()}\n{'='*80}\n")
            self.conversation_log.flush()
        
        return reply
    
    # ==================================================================
    # Internal
    # ==================================================================
    def _process_reply(self, reply: ChatGuideReply):
        """Process LLM reply and update state."""
        self._executed_routes.clear()

        # Process batch tasks
        for task_result in reply.tasks:
            task_id = task_result.task_id
            result = task_result.result.strip()
            
            if task_id in self.state.get_current_tasks():
                self.state.tracker.increment_attempt(task_id)
            
            if result:
                self.state.tracker.results[task_id] = result
                self.state.tracker.status[task_id] = "completed"
                self._log(f"Task '{task_id}': {result}")

        # Process persistent tasks
        for task_result in reply.persistent_tasks:
            if task_result.result.strip():
                self.state.tracker.results[task_result.task_id] = task_result.result.strip()
        
        # Execute routes
        self._process_routes()

        # Update history
        self.state.conversation.add_message(
            self.state.participants.chatbot,
            reply.assistant_reply
        )
        
        # Try to advance
        if not self.state.get_current_tasks():
            self.state.flow.advance()
    
    def _process_routes(self):
        """Check and execute routes."""
        for i, route in enumerate(self.routes):
            condition = route.get("condition", "")
            route_id = f"route_{i}"
            
            if route_id in self._executed_routes:
                continue
    
            # Build context
            context = {
                "task_results": self.state.tracker.results,
                "turn_count": self.state.interaction.turn_count,
                "batch_index": self.state.flow.current_index,
                "task_attempts": dict(self.state.tracker.attempts),
                "current_tasks": self.state.get_current_tasks(),
                "user_name": self.state.participants.user,
                "chatbot_name": self.state.participants.chatbot,
            }
            
            # Evaluate and execute
            if RouteEvaluator.evaluate(condition, context):
                if self._route_executor.execute(route):
                    self._executed_routes.add(route_id)
                    break
    
    def _log(self, message: str):
        """Log message."""
        if self.debug and self.logger:
            self.logger.info(message)
    
    # ==================================================================
    # Utility & Debug
    # ==================================================================
    def get_state(self) -> dict:
        """Get full state as dict."""
        return self.state.to_dict()
    
    def get_prompt(self) -> str:
        """Get current prompt for debugging."""
        return PromptBuilder(self.config, self.state).build()
    
    def print_debug(self, show_prompt: bool = False) -> str:
        """Get beautiful formatted debug output.
        
        Args:
            show_prompt: If True, include full prompt in output
            
        Returns:
            Formatted debug string
        """
        prompt = self.get_prompt() if show_prompt else ""
        return DebugFormatter.format_state(self.get_state(), show_prompt, prompt)
    
    def print_debug_compact(self) -> str:
        """Get compact one-line debug output."""
        return DebugFormatter.format_compact(self.get_state())
    
    @staticmethod
    def print_response(reply: ChatGuideReply, show_tasks: bool = True) -> str:
        """Get beautifully formatted AI response.
        
        Args:
            reply: ChatGuideReply object
            show_tasks: If True, show task breakdown
            
        Returns:
            Formatted response string
        """
        return ResponseFormatter.format_reply(reply, show_tasks)

