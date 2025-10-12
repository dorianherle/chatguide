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

PERSISTENT TASKS:
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

==============================================================================='''.strip()
    
    def _format_memory(self) -> str:
        """Format memory with task results."""
        parts = [self.state.conversation.memory]
        
        if self.state.tracker.results:
            info_lines = [
                f"- {tid}: {res}"
                for tid, res in self.state.tracker.results.items()
                if res and tid not in ["detect_info_updates", "introduce_yourself"]
            ]
            if info_lines:
                parts.append("Known info:\n" + "\n".join(info_lines))
        
        return "\n".join(parts)
    
    def _format_history(self) -> str:
        """Format recent chat history."""
        return "\n".join(self.state.conversation.get_recent_history())
    
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
            for t in self.state.interaction.tones
        ]
        return " ".join(instructions)
