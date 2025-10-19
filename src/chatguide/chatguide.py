"""ChatGuide - main orchestrator."""

import asyncio
from typing import List, Dict, Any, Optional
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


class ChatGuide:
    """State-driven conversational agent framework.
    
    The LLM performs reasoning through tasks,
    the runtime executes tools using data from state,
    and adjustments keep the plan dynamic and reactive.
    """
    
    def __init__(self, api_key: str = None, debug: bool = False, language: str = "en"):
        # Core components
        self.state = State()
        self.plan = Plan()
        self.tasks: Dict[str, TaskDefinition] = {}
        self.adjustments = Adjustments()
        self.tool_registry = get_tool_registry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        
        # Tone and config
        self.tone: List[str] = []
        self.tone_definitions: Dict[str, str] = {}
        self.guardrails: str = ""
        self.language: str = language
        
        # Conversation
        self.conversation_history: List[Dict[str, str]] = []
        
        # Tracking
        self._last_fired_adjustments: List[str] = []
        
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
        # 1. Update state with task results
        for task_result in reply.task_results:
            self.state.set(task_result.key, task_result.value)
        
        # 2. Execute tools
        for tool_call in reply.tools:
            # Build args from tool call
            args = {}
            if tool_call.options:
                args['options'] = tool_call.options
            
            # Execute tool
            output = await self.tool_executor.execute(tool_call.tool, args)
            
            # Merge output into state
            if output:
                self.state.update(output)
        
        # 3. Evaluate adjustments
        fired_adjustments = self.adjustments.evaluate(self.state, self.plan, self.tone)
        
        # Store fired adjustments for UI display
        if fired_adjustments:
            if not hasattr(self, '_last_fired_adjustments'):
                self._last_fired_adjustments = []
            self._last_fired_adjustments = fired_adjustments
        
        # 4. Add assistant message to history (only if not silent)
        if not is_silent:
            self.add_assistant_message(reply.assistant_reply)
        
        # 5. Check if current block is complete
        current_block = self.plan.get_current_block()
        if self._is_block_complete(current_block, reply):
            self.plan.advance()
    
    def _is_block_complete(self, block: List[str], reply: ChatGuideReply) -> bool:
        """Check if all tasks in block have been completed."""
        # Simple heuristic: block complete if all tasks have results
        completed_tasks = {tr.task_id for tr in reply.task_results}
        return all(task_id in completed_tasks for task_id in block)
    
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
    
    def get_state(self) -> dict:
        """Get full state for debugging."""
        return {
            "state": self.state.to_dict(),
            "plan": self.plan.to_dict(),
            "tone": self.tone,
            "adjustments": self.adjustments.to_dict(),
            "history_length": len(self.conversation_history),
            "last_fired_adjustments": self._last_fired_adjustments
        }
    
    def get_last_fired_adjustments(self) -> List[str]:
        """Get adjustments that fired in last turn."""
        return self._last_fired_adjustments.copy()
    
    def clear_fired_adjustments(self):
        """Clear the last fired adjustments tracking."""
        self._last_fired_adjustments = []
