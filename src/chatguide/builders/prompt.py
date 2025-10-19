"""Prompt builder - assembles LLM prompts."""

from typing import List, Dict, Any
import yaml
from pathlib import Path

from ..core.config import Config
from ..core.state import ConversationState


class PromptBuilder:
    """Builds prompts from config and state."""
    
    # Cache for core prompt templates
    _core_prompts: Dict[str, Dict[str, Any]] = None
    
    def __init__(self, config: Config, state: ConversationState):
        self.config = config
        self.state = state
        
        # Load core prompts on first use
        if PromptBuilder._core_prompts is None:
            PromptBuilder._load_core_prompts()
    
    @classmethod
    def _load_core_prompts(cls):
        """Load core prompt templates from YAML."""
        core_prompt_path = Path(__file__).parent.parent / "core" / "core_prompt.yaml"
        with open(core_prompt_path, 'r', encoding='utf-8') as f:
            cls._core_prompts = yaml.safe_load(f)
    
    def _get_template(self) -> Dict[str, Any]:
        """Get template for current language, fallback to English."""
        lang = self.state.language
        return self._core_prompts.get(lang, self._core_prompts['en'])
    
    def build(self) -> str:
        """Build complete prompt with language support."""
        t = self._get_template()
        
        # Format critical rules
        rules = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(t['critical_rules'])])
        rules = rules.replace("{count}", str(len(self.state.get_persistent_tasks())))
        
        return f'''
{t['language_instruction']}

{t['memory_header']}
{self._format_memory()}

{t['chat_history_header']}
{self._format_history()}

{t['guardrails_header']}
{self.config.guardrails}

{t['current_tasks_header']}
{self._format_tasks(self.state.get_current_tasks())}

{t['persistent_tasks_header']}
{self._format_tasks(self.state.get_persistent_tasks())}

{t['next_tasks_header']}
{self._format_next_tasks()}

{t['tone_header']} {self._format_tone()}

{t['output_format_header']}
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

{t['critical_rules_header']}
{rules}

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
            t = self._get_template()
            return t['none']
        
        lines = []
        for tid in task_ids:
            desc = self.config.get_task_description(tid)
            lines.append(f"{tid}: {desc}")
        
        return "\n".join(lines)
    
    def _format_next_tasks(self) -> str:
        """Format next batch."""
        next_batch = self.state.flow.get_next_batch()
        if not next_batch:
            t = self._get_template()
            return t['no_next_tasks']
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
    
