"""Prompt builder - assembles LLM prompts."""

from typing import List

from ..core.config import Config
from ..core.state import ConversationState


class PromptBuilder:
    """Builds prompts from config and state."""
    
    def __init__(self, config: Config, state: ConversationState):
        self.config = config
        self.state = state
    
    def build(self) -> str:
        """Build complete prompt."""
        return f'''
MEMORY:
{self._format_memory()}

CHAT HISTORY:
{self._format_history()}

GUARDRAILS:
{self.config.guardrails}

CURRENT TASKS:
{self._format_tasks(self.state.get_current_tasks())}

PERSISTENT TASKS (MUST return ALL in EVERY response):
{self._format_tasks(self.state.get_persistent_tasks())}

NEXT TASKS:
{self._format_next_tasks()}

TONE: {self._format_tone()}

OUTPUT FORMAT:
{{
  "tasks": [
    {{
      "task_id": "task_name",
      "result": "output_value"
    }}
  ],
  "persistent_tasks": [
{self._format_persistent_output()}
  ],
  "assistant_reply": "your_response_here"
}}

CRITICAL RULES:
1. ALWAYS return ALL {len(self.state.get_persistent_tasks())} persistent tasks in EVERY response
2. Once all CURRENT TASKS are completed, IMMEDIATELY advance to NEXT TASKS
3. Return empty string for tasks not completed

==============================================================================='''.strip()
    
    def _format_memory(self) -> str:
        """Format memory with task results."""
        parts = [self.state.conversation.memory]
        
        if self.state.tasks.results:
            info_lines = [
                f"- {tid}: {res}"
                for tid, res in self.state.tasks.results.items()
                if res and tid not in ["detect_info_updates", "introduce_yourself"]
            ]
            if info_lines:
                parts.append("Known info:\n" + "\n".join(info_lines))
        
        return "\n".join(parts)
    
    def _format_history(self) -> str:
        """Format recent chat history with dynamic name resolution."""
        history = self.state.conversation.get_recent_history()
        formatted = []
        for msg in history:
            role = msg["role"]
            text = msg["text"]
            # Resolve current participant names dynamically
            if role == self.state.participants.user or role == "user":
                role = self.state.participants.user
            elif role == self.state.participants.chatbot or role == "assistant":
                role = self.state.participants.chatbot
            formatted.append(f"{role}: {text}")
        return "\n".join(formatted)
    
    def _format_tasks(self, task_ids: List[str]) -> str:
        """Format task list with descriptions."""
        if not task_ids:
            return "None"
        
        lines = []
        for tid in task_ids:
            desc = self.config.get_task_description(tid)
            lines.append(f"{tid}: {desc}")
        
        return "\n".join(lines)
    
    def _format_next_tasks(self) -> str:
        """Format next batch."""
        next_batch = self.state.flow.get_next_batch()
        if not next_batch:
            return "No next tasks"
        return self._format_tasks(next_batch)
    
    def _format_tone(self) -> str:
        """Format active tones."""
        instructions = [
            self.config.tones.get(t, t) 
            for t in self.state.tones.active
        ]
        return " ".join(instructions)
    
    def _format_persistent_output(self) -> str:
        """Format persistent tasks for OUTPUT FORMAT example.
        
        Dynamically builds the example based on active persistent tasks.
        """
        persistent = self.state.get_persistent_tasks()
        if not persistent:
            return ""
        
        lines = []
        for i, task_id in enumerate(persistent):
            desc = self.config.get_task_description(task_id)
            # Extract hint from description if available
            hint = "result_value"
            if "Choose:" in desc:
                # Enum task - show options
                hint = desc.split("Choose:")[1].split(",")[0].strip() + "..."
            elif task_id == "detect_info_updates":
                hint = "update: task_id = value OR empty_string"
            
            comma = "," if i < len(persistent) - 1 else ""
            lines.append(f'    {{\n      "task_id": "{task_id}",\n      "result": "{hint}"\n    }}{comma}')
        
        return "\n".join(lines)
