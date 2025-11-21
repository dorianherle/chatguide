"""ChatGuide - main orchestrator."""

import asyncio
import json
import pickle
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from .state import State
from .plan import Plan
from .adjustments import Adjustments, Adjustment
from .tool_executor import ToolRegistry, ToolExecutor, get_tool_registry
from .schemas import TaskDefinition, ChatGuideReply, ToolCall
from .builders.prompt import PromptBuilder
from .io.llm import run_llm
from .utils.config_loader import (
    load_config_file, parse_state, parse_plan, parse_tasks,
    parse_tools, parse_adjustments, parse_tone, parse_tones, parse_guardrails
)
from .utils.response_parser import parse_llm_response
from .utils.logger import ChatGuideLogger


class ChatGuide:
    """State-driven conversational agent framework.
    
    The LLM performs reasoning through tasks,
    the runtime executes tools using data from state,
    and adjustments keep the plan dynamic and reactive.
    """
    
    def __init__(self, api_key: str = None, debug: bool = False, language: str = "en", 
                 log_format: str = "json", log_file: Optional[str] = None):
        # Core components
        self.state = State()
        self.plan = Plan()
        self.tasks: Dict[str, TaskDefinition] = {}
        self.adjustments = Adjustments()
        self.tool_registry = get_tool_registry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        
        # Logger
        self.logger = ChatGuideLogger(
            level=logging.DEBUG if debug else logging.INFO,
            format_type=log_format,
            output_file=log_file
        ) if debug or log_file else None
        
        # Tone and config
        self.tone: List[str] = []
        self.tone_definitions: Dict[str, str] = {}
        self.guardrails: str = ""
        self.language: str = language
        
        # Conversation
        self.conversation_history: List[Dict[str, str]] = []
        
        # Tracking
        self._last_fired_adjustments: List[str] = []
        self._completed_tasks: List[str] = []  # Track completed task IDs
        self._execution_status: str = "idle"  # idle | processing | awaiting_input | complete
        self._data_extractions: Dict[str, Dict[str, Any]] = {}  # Track what data was extracted by which task
        self._last_response: Optional[ChatGuideReply] = None  # Last LLM response
        self._last_response_silent: bool = False  # Was last response silent
        self._errors: List[Dict[str, Any]] = []  # Error log
        self._retry_count: int = 0  # Retry counter
        self._session_id: Optional[str] = None  # Session identifier
        self._session_metadata: Dict[str, Any] = {}  # Custom session data
        
        # Streaming callbacks
        self._stream_callbacks: List[Callable] = []
        
        # Middleware/Plugins
        self._middleware: List[Callable] = []  # Pre/post hooks
        self._task_hooks: Dict[str, List[Callable]] = {}  # Task-specific hooks
        
        # Metrics
        self._metrics: Dict[str, Any] = {
            "llm_calls": 0,
            "tokens_used": 0,
            "total_duration_ms": 0,
            "task_completions": 0,
            "errors": 0
        }
        
        # Settings
        self.api_key = api_key
        self.debug = debug
    
    def load_config(self, path: str):
        """Load configuration from YAML file."""
        data = load_config_file(path)
        
        # Parse state
        initial_state = parse_state(data)
        self.state = State(initial_state)
        
        # Parse plan
        plan_blocks = parse_plan(data)
        self.plan = Plan(plan_blocks)
        
        # Parse tasks
        self.tasks = parse_tasks(data)
        
        # Parse tools
        tool_defs = parse_tools(data)
        for tool_id, tool_data in tool_defs.items():
            self.tool_registry.register(
                tool_id,
                tool_data.get("type", "function"),
                tool_data.get("description", "")
            )
        
        # Parse adjustments
        adjustments = parse_adjustments(data)
        for adj in adjustments:
            self.adjustments.add(adj)
        
        # Parse tone
        self.tone = parse_tone(data)
        self.tone_definitions = parse_tones(data)
        
        # Parse guardrails
        self.guardrails = parse_guardrails(data)
        
        # Parse language (optional)
        if "language" in data:
            self.language = data["language"]
    
    def add_user_message(self, message: str):
        """Add user message to history."""
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
    
    def add_assistant_message(self, message: str):
        """Add assistant message to history."""
        self.conversation_history.append({
            "role": "assistant",
            "content": message
        })
    
    async def chat_async(
        self,
        model: str = "gemini/gemini-2.0-flash-exp",
        api_key: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> ChatGuideReply:
        """Execute one chat turn (async)."""
        # Update status
        self._execution_status = "processing"
        
        # Run before middleware
        context = self._run_middleware("before", {
            "state": self.state.to_dict(),
            "plan": self.plan.to_dict(),
            "current_task": self.get_current_task(),
            "conversation_history": self.conversation_history
        })
        
        # Check if ANY current task is silent (not all)
        current_tasks = self.plan.get_current_block()
        has_silent_task = any(
            self.tasks.get(task_id, TaskDefinition(description="")).silent 
            for task_id in current_tasks
        ) if current_tasks else False
        
        # Build prompt
        prompt = PromptBuilder(
            self.state,
            self.plan,
            self.tasks,
            self.tone,
            self.tone_definitions,
            self.guardrails,
            self.conversation_history,
            self.language
        ).build()
        
        # Call LLM
        key = api_key or self.api_key
        raw = run_llm(
            prompt,
            model=model,
            api_key=key,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_config={"response_schema": ChatGuideReply.model_json_schema()}
        )
        
        # Parse response
        reply = parse_llm_response(raw)
        
        # Check if THIS specific reply is for a silent task
        is_this_silent = False
        if reply.task_results:
            for task_result in reply.task_results:
                task_def = self.tasks.get(task_result.task_id)
                if task_def and task_def.silent:
                    is_this_silent = True
                    break
        
        # Process reply (may be silent)
        await self._process_reply(reply, is_silent=is_this_silent)
        
        # If silent, immediately call again with new tone/state
        if is_this_silent:
            # Build new prompt with updated state/tone
            prompt_updated = PromptBuilder(
                self.state,
                self.plan,
                self.tasks,
                self.tone,
                self.tone_definitions,
                self.guardrails,
                self.conversation_history,
                self.language
            ).build()
            
            # Call LLM again
            raw_updated = run_llm(
                prompt_updated,
                model=model,
                api_key=key,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_config={"response_schema": ChatGuideReply.model_json_schema()}
            )
            
            reply = parse_llm_response(raw_updated)
            await self._process_reply(reply, is_silent=False)
        
        return reply
    
    def chat(
        self,
        model: str = "gemini/gemini-2.0-flash-exp",
        api_key: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> ChatGuideReply:
        """Execute one chat turn (sync wrapper)."""
        return asyncio.run(self.chat_async(model, api_key, temperature, max_tokens))
    
    async def _process_reply(self, reply: ChatGuideReply, is_silent: bool = False):
        """Process LLM reply - core runtime loop."""
        import time
        start_time = time.time()
        
        # Store last response
        self._last_response = reply
        self._last_response_silent = is_silent
        
        # Update metrics
        self._metrics["llm_calls"] += 1
        
        # Emit LLM response event
        self._emit_event({
            "type": "llm_response",
            "reply": reply.assistant_reply,
            "was_silent": is_silent,
            "task_results": [{"task_id": tr.task_id, "key": tr.key} for tr in reply.task_results]
        })
        
        # Log LLM response
        if self.logger:
            self.logger.llm_response(
                reply.assistant_reply, 
                is_silent, 
                [{"task_id": tr.task_id, "key": tr.key} for tr in reply.task_results]
            )
        
        # 1. Update state with task results
        for task_result in reply.task_results:
            # Emit task start event
            self._emit_event({
                "type": "task_complete",
                "task_id": task_result.task_id,
                "key": task_result.key,
                "value": task_result.value
            })
            
            self.state.set(task_result.key, task_result.value)
            # Track completed tasks
            if task_result.task_id not in self._completed_tasks:
                self._completed_tasks.append(task_result.task_id)
                self._metrics["task_completions"] += 1
                
                # Run task hooks
                self._run_task_hooks(task_result.task_id, task_result.value)
            
            # Track data extraction
            self._data_extractions[task_result.key] = {
                "value": task_result.value,
                "extracted_by": task_result.task_id,
                "validated": True  # Assume validated if LLM extracted it
            }
        
        # 2. Execute tools
        for tool_call in reply.tools:
            # Emit tool call event
            self._emit_event({
                "type": "tool_call",
                "tool": tool_call.tool,
                "options": tool_call.options
            })
            
            # Build args from tool call
            args = {}
            if tool_call.options:
                args['options'] = tool_call.options
            
            try:
                # Execute tool
                output = await self.tool_executor.execute(tool_call.tool, args)
                
                # Merge output into state
                if output:
                    self.state.update(output)
            except Exception as e:
                # Track errors
                error_data = {
                    "type": "tool_execution",
                    "tool": tool_call.tool,
                    "error": str(e),
                    "task": self.get_current_task(),
                    "timestamp": datetime.now().isoformat()
                }
                self._errors.append(error_data)
                self._metrics["errors"] += 1
                
                # Emit error event
                self._emit_event({
                    "type": "error",
                    **error_data
                })
                
                if self.debug:
                    print(f"[ERROR] Tool execution failed: {tool_call.tool} - {e}")
        
        # 3. Evaluate adjustments
        fired_adjustments = self.adjustments.evaluate(self.state, self.plan, self.tone)
        
        # Store fired adjustments for UI display
        if fired_adjustments:
            if not hasattr(self, '_last_fired_adjustments'):
                self._last_fired_adjustments = []
            self._last_fired_adjustments = fired_adjustments
            
            # Emit adjustment fired events
            for adj_name in fired_adjustments:
                # Find the adjustment object
                adj_obj = next((a for a in self.adjustments._adjustments if a.name == adj_name), None)
                self._emit_event({
                    "type": "adjustment_fired",
                    "name": adj_name,
                    "actions": adj_obj.actions if adj_obj else []
                })
        
        # 4. Add assistant message to history (only if not silent)
        if not is_silent:
            self.add_assistant_message(reply.assistant_reply)
        
        # 4.5. Auto-complete tasks with no expectations
        current_block = self.plan.get_current_block()
        for task_id in current_block:
            task_def = self.tasks.get(task_id)
            # If task exists, has no expectations, and we have a reply
            if task_def and not task_def.expects:
                if task_id not in self._completed_tasks:
                    self._completed_tasks.append(task_id)
                    self._metrics["task_completions"] += 1
        
        # 5. Check if current block is complete
        if self._is_block_complete(current_block, reply):
            self.plan.advance()
        
        # 6. Update execution status
        if self.plan.is_finished():
            self._execution_status = "complete"
        else:
            self._execution_status = "awaiting_input"
        
        # Update timing metrics
        duration_ms = (time.time() - start_time) * 1000
        self._metrics["total_duration_ms"] += duration_ms
    
    def _is_block_complete(self, block: List[str], reply: ChatGuideReply) -> bool:
        """Check if all tasks in block have been completed."""
        # Check against global completed tasks
        return all(task_id in self._completed_tasks for task_id in block)
    
    def get_pending_ui_tools(self) -> list:
        """Get pending UI tools to render."""
        return self.tool_executor.get_pending_ui_tools()
    
    def handle_tool_response(self, tool_id: str, result: Any):
        """Handle response from UI tool."""
        # Add as user message
        if isinstance(result, dict):
            self.state.update(result)
            self.add_user_message(str(result))
        else:
            self.add_user_message(str(result))
    
    def is_finished(self) -> bool:
        """Check if plan is complete."""
        return self.plan.is_finished()
    
    def _get_all_tasks(self) -> List[str]:
        """Get all task IDs from plan."""
        all_tasks = []
        for block in self.plan._blocks:
            all_tasks.extend(block)
        return all_tasks
    
    def _get_pending_tasks(self) -> List[str]:
        """Get all tasks that haven't been completed yet."""
        all_tasks = self._get_all_tasks()
        return [task for task in all_tasks if task not in self._completed_tasks]
    
    def _get_block_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all blocks with completion status."""
        metadata = []
        for index, block in enumerate(self.plan._blocks):
            all_completed = all(task in self._completed_tasks for task in block)
            any_completed = any(task in self._completed_tasks for task in block)
            
            if index < self.plan.current_index:
                status = "completed"
            elif index == self.plan.current_index:
                status = "in_progress" if any_completed else "current"
            else:
                status = "pending"
            
            metadata.append({
                "index": index,
                "tasks": block,
                "status": status,
                "completed": all_completed
            })
        return metadata
    
    def _get_task_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all tasks with status and definitions."""
        task_meta = {}
        for task_id, task_def in self.tasks.items():
            status = "completed" if task_id in self._completed_tasks else "pending"
            if task_id == self.get_current_task():
                status = "in_progress"
            
            task_meta[task_id] = {
                "status": status,
                "description": task_def.description,
                "expects": task_def.expects,
                "has_tools": len(task_def.tools) > 0,
                "tool_count": len(task_def.tools),
                "is_silent": task_def.silent
            }
        return task_meta
    
    def _get_expected_keys(self) -> List[str]:
        """Get all keys that tasks expect to extract."""
        expected = []
        for task_def in self.tasks.values():
            expected.extend(task_def.expects)
        return list(set(expected))  # Remove duplicates
    
    def _get_data_coverage(self) -> Dict[str, Any]:
        """Analyze data coverage - expected vs collected keys."""
        expected_keys = self._get_expected_keys()
        collected_keys = list(self.state.to_dict().keys())
        missing_keys = [k for k in expected_keys if k not in collected_keys]
        
        return {
            "expected_keys": expected_keys,
            "collected_keys": collected_keys,
            "missing_keys": missing_keys,
            "coverage_percent": int((len(collected_keys) / len(expected_keys) * 100)) if expected_keys else 100
        }
    
    def get_state(self) -> dict:
        """Get comprehensive execution state.
        
        Returns complete snapshot of execution including:
        - execution: current position, status, pending tools, errors
        - progress: task completion tracking with metadata
        - tasks: individual task status and definitions
        - data: extracted state variables with tracking
        - data_coverage: expected vs collected analysis
        - tone: current expression style
        - adjustments: fired and pending rules
        - conversation: turn counts and last messages
        - last_response: metadata from last LLM call
        """
        current_block = self.plan.get_current_block()
        all_tasks = self._get_all_tasks()
        pending_ui_tools = self.get_pending_ui_tools()
        
        # Get last messages
        last_user_msg = None
        last_assistant_msg = None
        for msg in reversed(self.conversation_history):
            if msg['role'] == 'user' and last_user_msg is None:
                last_user_msg = msg['content']
            if msg['role'] == 'assistant' and last_assistant_msg is None:
                last_assistant_msg = msg['content']
            if last_user_msg and last_assistant_msg:
                break
        
        state = {
            "execution": {
                "current_block_index": self.plan.current_index,
                "current_tasks": current_block,
                "is_finished": self.plan.is_finished(),
                "status": self._execution_status,
                "pending_ui_tools": pending_ui_tools,
                "waiting_for_tool": pending_ui_tools[0] if pending_ui_tools else None,
                "errors": self._errors.copy(),
                "error_count": len(self._errors),
                "retry_count": self._retry_count
            },
            "progress": {
                "completed_tasks": self._completed_tasks.copy(),
                "pending_tasks": self._get_pending_tasks(),
                "total_tasks": len(all_tasks),
                "completed_count": len(self._completed_tasks),
                "blocks": self._get_block_metadata()
            },
            "tasks": self._get_task_metadata(),
            "data": self.state.to_dict(),
            "data_extractions": self._data_extractions.copy(),
            "data_coverage": self._get_data_coverage(),
            "tone": self.tone,
            "adjustments": {
                "fired": self._last_fired_adjustments.copy(),
                "all": self.adjustments.to_dict()
            },
            "conversation": {
                "turn_count": len(self.conversation_history),
                "user_message_count": len([m for m in self.conversation_history if m['role'] == 'user']),
                "assistant_message_count": len([m for m in self.conversation_history if m['role'] == 'assistant']),
                "last_user_message": last_user_msg,
                "last_assistant_message": last_assistant_msg
            }
        }
        
        # Add last response metadata if available
        if self._last_response:
            state["last_response"] = {
                "task_results": [
                    {"task_id": tr.task_id, "key": tr.key, "value": tr.value}
                    for tr in self._last_response.task_results
                ],
                "tools_called": [
                    {"tool": tc.tool, "options": tc.options}
                    for tc in self._last_response.tools
                ],
                "was_silent": self._last_response_silent,
                "assistant_reply": self._last_response.assistant_reply if not self._last_response_silent else None
            }
        
        return state
    
    def get_current_task(self) -> Optional[str]:
        """Get the current task being executed.
        
        Returns the first incomplete task in the current block,
        or None if block is complete or plan is finished.
        """
        if self.plan.is_finished():
            return None
        
        current_block = self.plan.get_current_block()
        for task in current_block:
            if task not in self._completed_tasks:
                return task
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """Get simple progress metrics.
        
        Returns:
            {
                "completed": 2,
                "total": 8,
                "percent": 25,
                "current_task": "get_age"
            }
        """
        all_tasks = self._get_all_tasks()
        total = len(all_tasks)
        completed = len(self._completed_tasks)
        percent = int((completed / total * 100)) if total > 0 else 0
        
        return {
            "completed": completed,
            "total": total,
            "percent": percent,
            "current_task": self.get_current_task()
        }
    
    def get_next_tasks(self, limit: int = 3) -> List[str]:
        """Get upcoming tasks.
        
        Args:
            limit: Maximum number of tasks to return
        
        Returns:
            List of upcoming task IDs
        """
        pending = self._get_pending_tasks()
        return pending[:limit]
    
    def is_waiting_for_user(self) -> bool:
        """Check if the guide is waiting for user input.
        
        Returns True if status is 'awaiting_input', False otherwise.
        """
        return self._execution_status == "awaiting_input"
    
    def get_last_fired_adjustments(self) -> List[str]:
        """Get adjustments that fired in last turn."""
        return self._last_fired_adjustments.copy()
    
    def clear_fired_adjustments(self):
        """Clear the last fired adjustments tracking."""
        self._last_fired_adjustments = []
    
    # ==================== SESSION PERSISTENCE ====================
    
    def checkpoint(self, include_config: bool = False) -> Dict[str, Any]:
        """Create a checkpoint of current session state.
        
        Args:
            include_config: Whether to include task/tool definitions (for full restore)
        
        Returns:
            Serializable checkpoint dict
        """
        checkpoint = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,
            "session_metadata": self._session_metadata,
            
            # Core state
            "state": self.state.to_dict(),
            "plan": {
                "blocks": self.plan._blocks,
                "current_index": self.plan.current_index
            },
            "tone": self.tone,
            
            # Tracking
            "completed_tasks": self._completed_tasks,
            "execution_status": self._execution_status,
            "data_extractions": self._data_extractions,
            "errors": self._errors,
            "retry_count": self._retry_count,
            "conversation_history": self.conversation_history,
            
            # Adjustments state
            "fired_adjustments": [adj.name for adj in self.adjustments._adjustments if adj.fired],
            
            # Metrics
            "metrics": self._metrics.copy()
        }
        
        if include_config:
            checkpoint["config"] = {
                "tasks": {tid: {"description": t.description, "expects": t.expects, 
                               "tools": t.tools, "silent": t.silent} 
                         for tid, t in self.tasks.items()},
                "tone_definitions": self.tone_definitions,
                "guardrails": self.guardrails,
                "language": self.language
            }
        
        return checkpoint
    
    @classmethod
    def from_checkpoint(cls, checkpoint: Dict[str, Any], api_key: str = None, debug: bool = False) -> "ChatGuide":
        """Restore a ChatGuide instance from a checkpoint.
        
        Args:
            checkpoint: Checkpoint dict from checkpoint()
            api_key: API key (required if not in checkpoint)
            debug: Debug mode
        
        Returns:
            Restored ChatGuide instance
        """
        # Create new instance
        cg = cls(api_key=api_key, debug=debug)
        
        # Restore core state
        cg.state = State(checkpoint["state"])
        cg.plan = Plan(checkpoint["plan"]["blocks"])
        cg.plan._current_index = checkpoint["plan"]["current_index"]
        cg.tone = checkpoint["tone"]
        
        # Restore tracking
        cg._completed_tasks = checkpoint["completed_tasks"]
        cg._execution_status = checkpoint["execution_status"]
        cg._data_extractions = checkpoint["data_extractions"]
        cg._errors = checkpoint["errors"]
        cg._retry_count = checkpoint["retry_count"]
        cg.conversation_history = checkpoint["conversation_history"]
        cg._session_id = checkpoint.get("session_id")
        cg._session_metadata = checkpoint.get("session_metadata", {})
        cg._metrics = checkpoint.get("metrics", {})
        
        # Restore config if included
        if "config" in checkpoint:
            cfg = checkpoint["config"]
            cg.tasks = {tid: TaskDefinition(**tdata) for tid, tdata in cfg["tasks"].items()}
            cg.tone_definitions = cfg["tone_definitions"]
            cg.guardrails = cfg["guardrails"]
            cg.language = cfg["language"]
        
        # Restore fired adjustments (mark them as fired)
        fired_names = checkpoint.get("fired_adjustments", [])
        for adj in cg.adjustments._adjustments:
            if adj.name in fired_names:
                adj.fired = True
        
        return cg
    
    def save_checkpoint(self, path: str, include_config: bool = True):
        """Save checkpoint to file.
        
        Args:
            path: File path (.json)
            include_config: Whether to include full config
        """
        checkpoint = self.checkpoint(include_config=include_config)
        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        if self.logger:
            self.logger.checkpoint_saved(path, self._session_id)
    
    @classmethod
    def load_checkpoint(cls, path: str, api_key: str = None, debug: bool = False) -> "ChatGuide":
        """Load checkpoint from file.
        
        Args:
            path: File path (.json)
            api_key: API key
            debug: Debug mode
        
        Returns:
            Restored ChatGuide instance
        """
        with open(path, 'r') as f:
            checkpoint = json.load(f)
        
        cg = cls.from_checkpoint(checkpoint, api_key=api_key, debug=debug)
        
        if cg.logger:
            cg.logger.checkpoint_loaded(path, cg._session_id)
        
        return cg
    
    def set_session_id(self, session_id: str):
        """Set session identifier for tracking."""
        self._session_id = session_id
    
    def set_session_metadata(self, metadata: Dict[str, Any]):
        """Set custom session metadata."""
        self._session_metadata.update(metadata)
    
    # ==================== STREAMING SUPPORT ====================
    
    def add_stream_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a streaming callback for real-time events.
        
        Callback receives events:
        - {"type": "task_start", "task_id": "...", "description": "..."}
        - {"type": "task_complete", "task_id": "...", "key": "...", "value": "..."}
        - {"type": "tool_call", "tool": "...", "args": {...}}
        - {"type": "adjustment_fired", "name": "...", "actions": [...]}
        - {"type": "error", "error": "...", "context": {...}}
        - {"type": "llm_response", "reply": "...", "was_silent": false}
        """
        self._stream_callbacks.append(callback)
    
    def _emit_event(self, event: Dict[str, Any]):
        """Emit event to all stream callbacks."""
        for callback in self._stream_callbacks:
            try:
                callback(event)
            except Exception as e:
                if self.debug:
                    print(f"[ERROR] Stream callback failed: {e}")
    
    # ==================== METRICS & TELEMETRY ====================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get session metrics and telemetry."""
        return {
            **self._metrics,
            "session_duration_s": self._metrics.get("total_duration_ms", 0) / 1000,
            "avg_response_time_ms": (self._metrics["total_duration_ms"] / self._metrics["llm_calls"]) 
                                    if self._metrics["llm_calls"] > 0 else 0,
            "success_rate": ((self._metrics["task_completions"] - self._metrics["errors"]) / 
                           self._metrics["task_completions"]) if self._metrics["task_completions"] > 0 else 1.0
        }
    
    def reset_metrics(self):
        """Reset metrics counters."""
        self._metrics = {
            "llm_calls": 0,
            "tokens_used": 0,
            "total_duration_ms": 0,
            "task_completions": 0,
            "errors": 0
        }
    
    # ==================== MIDDLEWARE & PLUGINS ====================
    
    def add_middleware(self, middleware: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Add middleware function that runs before/after each turn.
        
        Middleware signature: func(context: dict) -> dict
        Context includes: state, plan, current_task, etc.
        Middleware can modify context and return it.
        """
        self._middleware.append(middleware)
    
    def add_task_hook(self, task_id: str, hook: Callable[[str, Any], None]):
        """Add hook that runs when a specific task completes.
        
        Hook signature: func(task_id: str, value: Any) -> None
        """
        if task_id not in self._task_hooks:
            self._task_hooks[task_id] = []
        self._task_hooks[task_id].append(hook)
    
    def _run_middleware(self, phase: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run middleware chain.
        
        Args:
            phase: "before" or "after"
            context: Current execution context
        
        Returns:
            Modified context
        """
        context["phase"] = phase
        for middleware in self._middleware:
            try:
                result = middleware(context)
                if result:
                    context = result
            except Exception as e:
                if self.debug:
                    print(f"[ERROR] Middleware failed: {e}")
        return context
    
    def _run_task_hooks(self, task_id: str, value: Any):
        """Run hooks for a specific task."""
        if task_id in self._task_hooks:
            for hook in self._task_hooks[task_id]:
                try:
                    hook(task_id, value)
                except Exception as e:
                    if self.debug:
                        print(f"[ERROR] Task hook failed for {task_id}: {e}")
