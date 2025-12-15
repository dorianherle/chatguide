"""ChatGuide - main orchestrator."""

import asyncio
import json
import pickle
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path

from .state import State
from .plan import Plan
from .core.task import Task
from .core.block import Block
from .core.context import Context
from .core.execution import ExecutionState
from .core.audit import AuditLog
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
    
    def __init__(self, api_key: str = None, config: Any = None, debug: bool = False, 
                 language: str = "en", log_format: str = "json", log_file: Optional[str] = None):
        # Core 4-layer architecture
        self.audit = AuditLog()
        self.state = State(audit_log=self.audit)
        self.context = Context()
        self.execution = ExecutionState()
        self.plan = Plan()
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
        
        # Tracking
        self._last_fired_adjustments: List[str] = []
        self._last_response: Optional[ChatGuideReply] = None
        self._last_response_silent: bool = False
        self._errors: List[Dict[str, Any]] = []
        self._retry_count: int = 0
        
        # Session persistence attributes
        self._session_id: Optional[str] = None
        self._session_metadata: Dict[str, Any] = {}
        
        # Streaming callbacks
        self._stream_callbacks: List[Callable] = []
        
        # Middleware/Plugins
        self._middleware: List[Callable] = []
        self._task_hooks: Dict[str, List[Callable]] = {}
        
        # Metrics
        self._metrics: Dict[str, Any] = {
            "llm_calls": 0,
            "tokens_used": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_duration_ms": 0,
            "task_completions": 0,
            "errors": 0
        }
        
        # Settings
        self.api_key = api_key
        self.debug = debug
        
        # Auto-load config if provided
        if config:
            self.load_config(config)
    
    def load_config(self, config: Union[str, Dict[str, Any]]):
        """Load configuration from YAML file path or dict directly."""
        if isinstance(config, dict):
            data = config
        else:
            data = load_config_file(config)
        
        # Parse state
        initial_state = parse_state(data)
        self.state = State(initial_state)
        
        # Parse tasks definitions first
        task_defs = parse_tasks(data)
        
        # Parse plan blocks (list of lists of strings)
        raw_blocks = parse_plan(data)
        
        # Convert to Block and Task objects
        from .schemas import ExpectDefinition
        blocks = []
        for raw_block in raw_blocks:
            tasks = []
            for task_id in raw_block:
                if task_id in task_defs:
                    def_ = task_defs[task_id]
                    
                    # Normalize expects to ExpectDefinition objects at load time
                    # This eliminates runtime isinstance checks throughout the codebase
                    normalized_expects = []
                    for exp in def_.expects:
                        if isinstance(exp, str):
                            normalized_expects.append(ExpectDefinition(key=exp))
                        elif isinstance(exp, ExpectDefinition):
                            normalized_expects.append(exp)
                        elif isinstance(exp, dict):
                            normalized_expects.append(ExpectDefinition(**exp))
                        else:
                            normalized_expects.append(exp)
                    
                    tasks.append(Task(
                        id=task_id,
                        description=def_.description,
                        expects=normalized_expects,
                        tools=def_.tools,
                        silent=def_.silent
                    ))
                else:
                    # Create dummy task if not defined (should warn)
                    tasks.append(Task(id=task_id, description=""))
            blocks.append(Block(tasks))
            
        self.plan = Plan(blocks)
        
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

        # print the full parsed config
        if self.debug:
            print("config File: ")
            print("Tasks: ", len(task_defs))
            print("Blocks: ", len(blocks))
            print("Tools: ", len(tool_defs))
            print("Adjustments: ", len(adjustments))
            print("Tone: ", self.tone)
            print("Tone Definitions: ", self.tone_definitions)
            print("Guardrails: ", self.guardrails)
            print("Language: ", self.language)
    
    def add_user_message(self, message: str):
        """Add user message to history."""
        self.context.add_message("user", message)
    
    def add_assistant_message(self, message: str):
        """Add assistant message to history."""
        self.context.add_message("assistant", message)
    
    async def chat_async(
        self,
        model: str = "gemini/gemini-2.0-flash-exp",
        api_key: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> ChatGuideReply:
        """Execute one chat turn (async)."""
        self.execution.status = "processing"

        accumulated_reply: Optional[ChatGuideReply] = None

        while True:
            reply, should_continue, is_silent = await self._single_turn(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if is_silent:
                # Silent turns are internal; do not surface or merge them.
                pass
            elif accumulated_reply is None:
                accumulated_reply = reply
            else:
                accumulated_reply.assistant_reply = (
                    f"{accumulated_reply.assistant_reply}\n\n{reply.assistant_reply}"
                )
                accumulated_reply.task_results.extend(reply.task_results)
                accumulated_reply.tools.extend(reply.tools)

                if getattr(reply, "state_corrections", None):
                    if not getattr(accumulated_reply, "state_corrections", None):
                        accumulated_reply.state_corrections = []
                    accumulated_reply.state_corrections.extend(reply.state_corrections)

            if not should_continue:
                return accumulated_reply or reply

    async def _single_turn(
        self,
        model: str,
        api_key: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> tuple[ChatGuideReply, bool, bool]:
        self.execution.current_task = self.get_current_task()

        context = self._run_middleware("before", {
            "state": self.state.to_dict(),
            "plan": self.plan.to_dict(),
            "current_task": self.execution.current_task,
            "conversation_history": self.context.get_history_dict()
        })

        if self.logger:
            self.logger.log_event("execution_context", context)

        from .builders.prompt import PromptView, PromptBuilder

        current_block = self.plan.get_current_block()
        pending_tasks = []
        if current_block:
            pending_tasks = [t for t in current_block.tasks if not t.is_completed()]

        completed_ids = [t.id for t in self.plan.get_all_tasks() if t.is_completed()]
        
        # Get first task of next block for smooth transitions
        next_block_task = None
        next_block = self.plan.get_block(self.plan.current_index + 1)
        if next_block and next_block.tasks:
            next_block_task = next_block.tasks[0]

        if not self.tone:
            tone_text = "Natural and helpful"
        else:
            descriptions = []
            for tone_id in self.tone:
                desc = self.tone_definitions.get(tone_id, tone_id)
                descriptions.append(desc)
            tone_text = " ".join(descriptions)

        current_task_id = self.execution.current_task
        current_task = self.plan.get_task(current_task_id) if current_task_id else None

        view = PromptView(
            current_task=current_task,
            pending_tasks=pending_tasks,
            completed_tasks=completed_ids,
            state=self.state.to_dict(),
            tone_text=tone_text,
            guardrails=self.guardrails,
            history=self.context.get_history_dict(),
            language=self.language,
            next_block_task=next_block_task,
            recent_extractions=self.state.get_recent_extractions()
        )

        base_prompt = PromptBuilder(view).build()
        prompt = base_prompt

        retries = 0
        max_retries = 2
        last_error = None
        error_type = "unknown"

        while retries <= max_retries:
            if self.logger:
                self.logger.log_event("llm_prompt", {"prompt": prompt, "attempt": retries + 1})

            key = api_key or self.api_key
            try:
                result = run_llm(
                    prompt,
                    model=model,
                    api_key=key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_config={"response_schema": ChatGuideReply.model_json_schema()}
                )

                if result.usage:
                    self._metrics["prompt_tokens"] += result.usage.prompt
                    self._metrics["completion_tokens"] += result.usage.completion
                    self._metrics["tokens_used"] += (result.usage.prompt + result.usage.completion)

                raw_content = result.content
                reply = parse_llm_response(raw_content)

                validation_errors = []
                for tr in reply.task_results:
                    task = self.plan.get_task(tr.task_id) if tr.task_id else None
                    if task:
                        is_valid, error = task.validate(tr.key, tr.value)
                        if not is_valid:
                            validation_errors.append(
                                f"Value '{tr.value}' for '{tr.key}' is invalid: {error}"
                            )

                if validation_errors:
                    raise ValueError("\n".join(validation_errors))

                break

            except json.JSONDecodeError as e:
                last_error = str(e)
                error_type = "json"
            except ValueError as e:
                last_error = str(e)
                error_type = "validation"
            except Exception as e:
                last_error = str(e)
                error_type = "unknown"

            retries += 1
            if retries > max_retries:
                print(f"[ERROR] Max retries reached. Last error: {last_error}")
                reply = ChatGuideReply(
                    assistant_reply=f"I encountered an internal error: {last_error}",
                    task_results=[],
                    state_corrections=[],
                    tools=[]
                )
                break

            print(f"[WARN] LLM Attempt {retries} failed: {last_error}. Retrying...")
            self._retry_count += 1

            if error_type == "json":
                retry_instruction = "\n\nSYSTEM: Return ONLY valid JSON. No text."
            elif error_type == "validation":
                retry_instruction = f"\n\nSYSTEM: Fix the invalid value only: {last_error}"
            else:
                retry_instruction = (
                    f"\n\nSYSTEM: Your previous response failed validation:\n- Error: {last_error}"
                    "\nFix ONLY the invalid part and return valid JSON."
                )
            prompt = base_prompt + retry_instruction

        is_this_silent = False
        for tr in getattr(reply, "task_results", []) or []:
            task = self.plan.get_task(tr.task_id) if getattr(tr, "task_id", None) else None
            if task and task.silent:
                is_this_silent = True
                break

        start_block_idx = self.plan.current_index
        await self._process_reply(reply, is_this_silent)

        # Only auto-continue for silent tasks (internal processing)
        # Block advancement should wait for user input to avoid merged/duplicated responses
        should_continue = is_this_silent

        return reply, should_continue, is_this_silent
    
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
        
        # Get current task for tracking
        self.execution.current_task = self.get_current_task()
        current_task_id = self.execution.current_task
        
        # Emit LLM response event
        self._emit_event({
            "type": "llm_response",
            "reply": reply.assistant_reply,
            "was_silent": is_silent,
            "task_results": [{"key": tr.key} for tr in reply.task_results]
        })
        
        # Log LLM response
        if self.logger:
            self.logger.llm_response(
                reply.assistant_reply, 
                is_silent, 
                [tr.model_dump() if hasattr(tr, 'model_dump') else tr.__dict__ for tr in reply.task_results]
            )
        
        # 0. Apply explicit state corrections (do NOT affect tasks)
        for corr in getattr(reply, "state_corrections", []):
            old_value = self.state.get(corr.key)
            if old_value != corr.value:
                self.state.set(
                    corr.key,
                    corr.value,
                    source_task="correction"
                )
        
        # Acknowledge corrections (Optional but recommended)
        if getattr(reply, "state_corrections", []) and not is_silent:
            self.context.add_message(
                "assistant",
                "Thanks for the clarification — I’ve updated that."
            )

        # 1. Update state with task results
        # Note: Deduplication by (task_id, key) is done in parse_llm_response()
        for task_result in reply.task_results:
            # Find the task - prefer task_id, fallback to key matching
            task = None
            if task_result.task_id:
                # Direct lookup by task_id (authoritative)
                task = self.plan.get_task(task_result.task_id)
            
            # Fallback to key matching for backwards compatibility
            if not task:
                current_block = self.plan.get_current_block()
                if current_block:
                    for t in current_block.get_pending_tasks():
                        if task_result.key in t.get_expected_keys() or t.id == task_result.key:
                            task = t
                            break
            
            # Validate if we found a task with rules
            if task:
                is_valid, error = task.validate(task_result.key, task_result.value)
                if not is_valid:
                    error_msg = f"Validation failed for {task_result.key}: {error}"
                    print(f"[WARN] {error_msg}")
                    if self.logger:
                        self.logger.log_event("validation_error", {
                            "key": task_result.key, 
                            "value": task_result.value, 
                            "error": error
                        })
                    # Skip this result - do not save to state, do not complete task
                    continue

            # Emit task complete event (only if valid)
            self._emit_event({
                "type": "task_complete",
                "task_id": task.id if task else task_result.task_id,
                "key": task_result.key,
                "value": task_result.value
            })
            
            # Set state with source task for audit
            self.state.set(task_result.key, task_result.value, source_task=task.id if task else task_result.task_id)
            
            # Mark task as complete if found AND all requirements met (Item #6)
            if task and not task.is_completed():
                # Check for confirmation requirements
                requirements_met = True
                for exp in task.expects:
                    if hasattr(exp, 'confirm') and exp.confirm:
                        confirm_key = f"{exp.key}_confirmed"
                        # Check strict boolean True (not just truthy, though truthy is probably fine)
                        if self.state.get(confirm_key) is not True:
                            requirements_met = False
                            break
                            
                if requirements_met:
                    self._complete_task(task, task_result.key, task_result.value)
            else:
                if not task:
                    print(f"[DEBUG] Task not found or already completed for key {task_result.key}.")
        
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
                # Retry logic (Item #7)
                tool_def = self.tool_registry.get(tool_call.tool)
                is_ui = tool_def and tool_def.type == "ui"
                max_attempts = 2 if not is_ui else 1
                
                output = None
                for attempt in range(max_attempts):
                    try:
                        # Execute tool
                        output = await self.tool_executor.execute(tool_call.tool, args, timeout=10.0)
                        break
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            raise e
                        # Wait briefly before retry?
                        await asyncio.sleep(0.5)
                
                # Merge output into state
                if output:
                    self.state.update(output, source_task=current_task_id)
            except Exception as e:
                # Track errors
                error_data = {
                    "type": "tool_execution",
                    "tool": tool_call.tool,
                    "error": str(e),
                    "task": current_task_id,
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
        
        # 3. Auto-complete tasks with no expectations (BEFORE adjustments)
        # This ensures adjustments see the correct completion state
        current_block = self.plan.get_current_block()
        if current_block:
            for task in current_block.tasks:
                if not task.expects and not task.is_completed():
                    self._complete_task(task, "auto", True)
        
        # 4. Evaluate adjustments
        fired_adjustments = self.adjustments.evaluate(self.state, self.plan, self.tone)
        
        # CRITICAL: Recompute block reference after adjustments
        # Adjustments can insert/remove/jump blocks, invalidating old reference
        current_block = self.plan.get_current_block()
        self.execution.current_task = self.get_current_task()
        
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
        
        # 5. Add assistant message to history (only if not silent)
        if not is_silent:
            self.add_assistant_message(reply.assistant_reply)
        
        # 6. Silent task + correction: block auto-advance to force visible turn
        if is_silent and getattr(reply, "state_corrections", []):
            # Skip block advancement - require a visible turn before plan moves
            pass
        elif current_block and current_block.is_complete():
            # 7. Check if current block is complete and advance
            self.plan.advance()
            self.execution.current_task = self.get_current_task()
        
        # 8. Update execution status (single location for tool-related status)
        if self.plan.is_finished():
            self.execution.status = "complete"
        elif self.tool_executor.has_pending_ui_tools():
            self.execution.status = "waiting_tool"
        else:
            self.execution.status = "awaiting_input"
        
        # Update timing metrics
        duration_ms = (time.time() - start_time) * 1000
        self._metrics["total_duration_ms"] += duration_ms
        
        # 7. Check invariants (debug mode only)
        self._check_invariants()
    
    def get_pending_ui_tools(self) -> list:
        """Get pending UI tools to render."""
        return self.tool_executor.get_pending_ui_tools()
    
    def handle_tool_response(self, tool_id: str, result: Any):
        """Handle response from UI tool."""
        self.execution.status = "processing"
        # Add as user message
        if isinstance(result, dict):
            self.state.update(result)
            self.add_user_message(str(result))
        else:
            self.add_user_message(str(result))
        self.execution.current_task = self.get_current_task()
    
    def is_finished(self) -> bool:
        """Check if plan is complete."""
        return self.plan.is_finished()
    
    def _get_all_tasks(self) -> List[str]:
        """Get all task IDs from plan."""
        return [t.id for t in self.plan.get_all_tasks()]
    
    def _get_pending_tasks(self) -> List[str]:
        """Get all tasks that haven't been completed yet."""
        return [t.id for t in self.plan.get_all_tasks() if not t.is_completed()]
    
    def _get_block_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all blocks with completion status."""
        metadata = []
        for index, block in enumerate(self.plan._blocks):
            if index < self.plan.current_index:
                status = "completed"
            elif index == self.plan.current_index:
                status = "in_progress" if any(t.is_completed() for t in block.tasks) else "current"
            else:
                status = "pending"
            
            metadata.append({
                "index": index,
                "tasks": block.task_ids,
                "status": status,
                "completed": block.is_complete()
            })
        return metadata
    
    def _get_task_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all tasks with status and definitions."""
        task_meta = {}
        for task in self.plan.get_all_tasks():
            status = task.status
            if task.id == self.get_current_task():
                status = "in_progress"
            
            task_meta[task.id] = {
                "status": status,
                "description": task.description,
                "expects": task.expects,
                "has_tools": len(task.tools) > 0,
                "tool_count": len(task.tools),
                "is_silent": task.silent
            }
        return task_meta
    
    def _get_expected_keys(self) -> List[str]:
        """Get all keys that tasks expect to extract."""
        expected = []
        for task in self.plan.get_all_tasks():
            expected.extend(task.get_expected_keys())
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
        current_tasks = current_block.task_ids if current_block else []
        all_tasks = self.plan.get_all_tasks()
        completed_tasks = [t.id for t in all_tasks if t.is_completed()]
        pending_ui_tools = self.get_pending_ui_tools()
        
        # Get last messages from context
        last_user_msg = None
        last_assistant_msg = None
        for msg in reversed(self.context.history):
            if msg.role == 'user' and last_user_msg is None:
                last_user_msg = msg.content
            if msg.role == 'assistant' and last_assistant_msg is None:
                last_assistant_msg = msg.content
            if last_user_msg and last_assistant_msg:
                break
        
        state = {
            "execution": {
                "current_block_index": self.plan.current_index,
                "current_tasks": current_tasks,
                "is_finished": self.plan.is_finished(),
                "status": self.execution.status,
                "pending_ui_tools": pending_ui_tools,
                "waiting_for_tool": pending_ui_tools[0] if pending_ui_tools else None,
                "errors": self._errors.copy(),
                "error_count": len(self._errors),
                "retry_count": self._retry_count
            },
            "progress": {
                "completed_tasks": completed_tasks,
                "pending_tasks": self._get_pending_tasks(),
                "total_tasks": len(all_tasks),
                "completed_count": len(completed_tasks),
                "blocks": self._get_block_metadata()
            },
            "tasks": self._get_task_metadata(),
            "data": self.state.variables,
            "data_coverage": self._get_data_coverage(),
            "tone": self.tone,
            "adjustments": {
                "fired": self._last_fired_adjustments.copy(),
                "all": self.adjustments.to_dict()
            },
            "conversation": {
                "turn_count": len(self.context.history),
                "user_message_count": len([m for m in self.context.history if m.role == 'user']),
                "assistant_message_count": len([m for m in self.context.history if m.role == 'assistant']),
                "last_user_message": last_user_msg,
                "last_assistant_message": last_assistant_msg
            }
        }
        
        # Add last response metadata if available
        if self._last_response:
            state["last_response"] = {
                "task_results": [
                    {"key": tr.key, "value": tr.value}
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
    
    def dump(self) -> Dict[str, Any]:
        """Export complete 4-layer data model for persistence.
        
        Returns:
            {
                "variables": {...},  # Business data
                "context": {...},    # Conversation history
                "execution": {...},  # Flow state
                "audit": [...]       # Change log
            }
        """
        return {
            "variables": self.state.variables,
            "context": self.context.to_dict(),
            "execution": self.execution.to_dict(),
            "audit": self.audit.to_list()
        }
    
    def get_current_task(self) -> Optional[str]:
        """Get the current task being executed.
        
        Returns the first incomplete task in the current block,
        or None if block is complete or plan is finished.
        """
        if self.plan.is_finished():
            return None
        
        current_block = self.plan.get_current_block()
        if not current_block:
            return None
            
        for task in current_block.tasks:
            if not task.is_completed():
                return task.id
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
        all_tasks = self.plan.get_all_tasks()
        total = len(all_tasks)
        completed = len([t for t in all_tasks if t.is_completed()])
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
    
    def get_next_blocks(self, limit: int = 3) -> List[List[str]]:
        """Get upcoming task blocks, filtering out completed tasks.
        
        Returns:
            List of blocks (lists of task IDs) that have pending tasks.
            Example: [['get_name', 'get_age'], ['get_origin']]
        """
        blocks = []
        # Start from current index
        for i in range(self.plan.current_index, len(self.plan._blocks)):
            block = self.plan._blocks[i]
            # Filter out completed tasks
            pending_in_block = [t.id for t in block.tasks if not t.is_completed()]
            
            if pending_in_block:
                blocks.append(pending_in_block)
            
            if len(blocks) >= limit:
                break
                
        return blocks
    
    def is_waiting_for_user(self) -> bool:
        """Check if the guide is waiting for user input.

        Returns True if status is 'awaiting_input', False otherwise.
        """
        return self.execution.status == "awaiting_input"
    
    def get_last_fired_adjustments(self) -> List[str]:
        """Get adjustments that fired in last turn."""
        return self._last_fired_adjustments.copy()
    
    def clear_fired_adjustments(self):
        """Clear the last fired adjustments tracking."""
        self._last_fired_adjustments = []
    
    def get_prompt(self) -> str:
        """Get the current prompt that would be sent to the LLM.
        
        Useful for debugging and inspection.
        """
        from .builders.prompt import PromptView, PromptBuilder

        # Calculate pending tasks in current block
        current_block = self.plan.get_current_block()
        pending_tasks = []
        if current_block:
            pending_tasks = [t for t in current_block.tasks if not t.is_completed()]
            
        # Calculate completed task IDs
        completed_ids = [t.id for t in self.plan.get_all_tasks() if t.is_completed()]
        
        # Calculate tone text
        if not self.tone:
            tone_text = "Natural and helpful"
        else:
            descriptions = []
            for tone_id in self.tone:
                desc = self.tone_definitions.get(tone_id, tone_id)
                descriptions.append(desc)
            tone_text = " ".join(descriptions)
            
        # Get current task object
        current_task_id = self.get_current_task()
        current_task = self.plan.get_task(current_task_id) if current_task_id else None
        
        # Get first task of next block for smooth transitions
        next_block_task = None
        next_block = self.plan.get_block(self.plan.current_index + 1)
        if next_block and next_block.tasks:
            next_block_task = next_block.tasks[0]
        
        view = PromptView(
            current_task=current_task,
            pending_tasks=pending_tasks,
            completed_tasks=completed_ids,
            state=self.state.to_dict(),
            tone_text=tone_text,
            guardrails=self.guardrails,
            history=self.context.get_history_dict(),
            language=self.language,
            next_block_task=next_block_task,
            recent_extractions=self.state.get_recent_extractions()
        )

        return PromptBuilder(view).build()

    
    def _run_middleware(self, phase: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run middleware hooks."""
        context['phase'] = phase
        for middleware in self._middleware:
            try:
                context = middleware(context)
            except Exception as e:
                print(f"[ERROR] Middleware failed: {e}")
        return context

    def add_middleware(self, middleware_func: Callable):
        """Add middleware function."""
        self._middleware.append(middleware_func)

    def add_task_hook(self, task_id: str, hook_func: Callable):
        """Add hook for specific task completion."""
        if task_id not in self._task_hooks:
            self._task_hooks[task_id] = []
        self._task_hooks[task_id].append(hook_func)

    def _run_task_hooks(self, task_id: str, value: Any):
        """Run hooks for a completed task."""
        if task_id in self._task_hooks:
            for hook in self._task_hooks[task_id]:
                try:
                    hook(task_id, value)
                except Exception as e:
                    print(f"[ERROR] Task hook failed for {task_id}: {e}")

    def _complete_task(self, task: "Task", key: str, value: Any):
        """Single authority for task completion - call this everywhere.
        
        This centralizes all task completion logic to ensure:
        - Task.status is updated
        - ExecutionState._completed is updated
        - Metrics are tracked
        - Hooks are run
        - Invariants are maintained
        """
        from .core.task import Task  # Local import to avoid circular
        
        # Invariant: task cannot complete twice
        if task.is_completed():
            if self.debug:
                print(f"[WARN] Attempted to complete already-completed task: {task.id}")
            return
        
        task.complete(key, value)
        self._metrics["task_completions"] += 1
        
        if self.debug:
            print(f"[DEBUG] Completed task {task.id} with key={key}, value={value}")
        
        # Run task hooks
        self._run_task_hooks(task.id, value)

    def _check_invariants(self):
        """Check structural invariants (debug mode only).
        
        Invariants checked:
        - Completed blocks must not contain pending tasks
        - Tasks marked in ExecutionState must also be Task.is_completed()
        """
        if not self.debug:
            return
        
        # Invariant 1: Completed blocks must not contain pending tasks
        for i in range(self.plan.current_index):
            block = self.plan.get_block(i)
            if block:
                pending = block.get_pending_tasks()
                if pending:
                    print(f"[INVARIANT VIOLATION] Completed block {i} has pending tasks: {[t.id for t in pending]}")
        
        # Invariant 2: Removed (ExecutionState no longer tracks completion - Task is SSoT)

    def add_stream_callback(self, callback: Callable):
        """Add callback for streaming events."""
        self._stream_callbacks.append(callback)

    def _emit_event(self, event: Dict[str, Any]):
        """Emit event to all callbacks."""
        for callback in self._stream_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"[ERROR] Stream callback failed: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self._metrics.copy()

    def reset_metrics(self):
        """Reset metrics to zero."""
        self._metrics = {
            "llm_calls": 0,
            "tokens_used": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_duration_ms": 0,
            "task_completions": 0,
            "errors": 0
        }

    # ==================== SESSION PERSISTENCE ====================
    
    def checkpoint(self, include_config: bool = False) -> Dict[str, Any]:
        """Create a checkpoint of current session state.
        
        Args:
            include_config: Whether to include task/tool definitions (for full restore)
        
        Returns:
            Serializable checkpoint dict
        """
        # Collect completed tasks from Plan objects
        completed_tasks = [t.id for t in self.plan.get_all_tasks() if t.is_completed()]
        
        checkpoint = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,
            "session_metadata": self._session_metadata,
            
            # Core state
            "state": self.state.to_dict(),
            "plan": {
                "blocks": [b.task_ids for b in self.plan._blocks], # Store as IDs for simpler serialization
                "current_index": self.plan.current_index
            },
            "tone": self.tone,
            
            # Tracking
            "completed_tasks": completed_tasks,
            "task_results": {t.id: t.result for t in self.plan.get_all_tasks() if t.result},
            "errors": self._errors,
            "retry_count": self._retry_count,
            "context": self.context.to_dict(),  # Save full context with history
            "execution": self.execution.to_dict(),  # Save execution state
            
            # Adjustments state
            "fired_adjustments": [adj.name for adj in self.adjustments._adjustments if adj.fired],
            
            # Metrics
            "metrics": self._metrics.copy()
        }
        
        if include_config:
            # Reconstruct tasks config from objects
            tasks_cfg = {}
            for task in self.plan.get_all_tasks():
                tasks_cfg[task.id] = {
                    "description": task.description,
                    "expects": task.expects,
                    "tools": task.tools,
                    "silent": task.silent
                }
                
            checkpoint["config"] = {
                "tasks": tasks_cfg,
                "tone_definitions": self.tone_definitions,
                "guardrails": self.guardrails,
                "language": self.language
            }
        
        return checkpoint
    
    @classmethod
    def from_checkpoint(cls, checkpoint: Dict[str, Any], api_key: str = None, debug: bool = False, 
                       log_file: Optional[str] = None, log_format: str = "json") -> "ChatGuide":
        """Restore a ChatGuide instance from a checkpoint.
        
        Args:
            checkpoint: Checkpoint dict from checkpoint()
            api_key: API key (required if not in checkpoint)
            debug: Debug mode
            log_file: Log file path
            log_format: Log format "json" or "text"
        
        Returns:
            Restored ChatGuide instance
            
        Note:
            If checkpoint has fired_adjustments but config was not included,
            you must call load_config() BEFORE from_checkpoint() to properly
            restore adjustment state. Otherwise, fired flags will be lost.
        """
        # Create new instance
        cg = cls(api_key=api_key, debug=debug, log_file=log_file, log_format=log_format)
        
        # Restore core state
        cg.state = State(checkpoint["state"])
        
        # Restore config if included
        task_defs = {}
        if "config" in checkpoint:
            cfg = checkpoint["config"]
            for tid, tdata in cfg["tasks"].items():
                task_defs[tid] = TaskDefinition(**tdata)
            cg.tone_definitions = cfg["tone_definitions"]
            cg.guardrails = cfg["guardrails"]
            cg.language = cfg["language"]
            
        # Restore plan
        # Note: We need task definitions to recreate Task objects
        # If config is not in checkpoint, we assume tasks are loaded separately or we create dummies
        # Ideally, user should load_config first if not included, but here we try to restore what we can
        
        raw_blocks = checkpoint["plan"]["blocks"]
        blocks = []
        completed_ids = checkpoint["completed_tasks"]
        
        for raw_block in raw_blocks:
            tasks = []
            for task_id in raw_block:
                # Use definition if available, else dummy
                if task_id in task_defs:
                    def_ = task_defs[task_id]
                    task = Task(
                        id=task_id,
                        description=def_.description,
                        expects=def_.expects,
                        tools=def_.tools,
                        silent=def_.silent
                    )
                else:
                    task = Task(id=task_id, description="")
            
                # Restore completion status and result (Item #9)
                task_results = checkpoint.get("task_results", {})
                if task_id in task_results:
                    task.result = task_results[task_id]
                    task.status = "completed"
                elif task_id in completed_ids:
                    # Backwards compatibility
                    task.status = "completed"
                    # Try to find value in state if possible, but for now just mark complete
                    
                tasks.append(task)
            blocks.append(Block(tasks))
            
        cg.plan = Plan(blocks)
        cg.plan._current_index = checkpoint["plan"]["current_index"]
        cg.tone = checkpoint["tone"]
        
        # Restore recent keys from state checkpoint
        if "state" in checkpoint and "recent_keys" in checkpoint["state"]:
            cg.state._recent_keys = checkpoint["state"]["recent_keys"]
        cg._errors = checkpoint.get("errors", [])
        cg._retry_count = checkpoint.get("retry_count", 0)
        
        # Restore execution state properly
        if "execution" in checkpoint:
            cg.execution = ExecutionState.from_dict(checkpoint["execution"])
        else:
            # Backwards compatibility: old checkpoints may not have execution
            cg.execution.status = "awaiting_input"

        cg.execution.current_task = cg.get_current_task()
        
        # Restore context (conversation history)
        if "context" in checkpoint:
            cg.context = Context.from_dict(checkpoint["context"])
        
        cg._session_id = checkpoint.get("session_id")
        cg._session_metadata = checkpoint.get("session_metadata", {})
        cg._metrics = checkpoint.get("metrics", {})
        
        # Restore fired adjustments
        fired_names = checkpoint.get("fired_adjustments", [])
        if fired_names and not cg.adjustments._adjustments:
            # Adjustments were fired but config not loaded - warn or fail
            import warnings
            warnings.warn(
                "Checkpoint has fired adjustments but no adjustments loaded. "
                "Call load_config() before from_checkpoint() to restore adjustment state properly.",
                RuntimeWarning
            )
        
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
    def load_checkpoint(cls, path: str, api_key: str = None, debug: bool = False,
                       log_file: Optional[str] = None, log_format: str = "json") -> "ChatGuide":
        """Load checkpoint from file.
        
        Args:
            path: File path (.json)
            api_key: API key
            debug: Debug mode
            log_file: Log file path
            log_format: Log format
        
        Returns:
            Restored ChatGuide instance
        """
        with open(path, 'r') as f:
            checkpoint = json.load(f)
        return cls.from_checkpoint(checkpoint, api_key, debug, log_file, log_format)
