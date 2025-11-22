"""Prompt builder - assembles LLM prompts from state."""

from typing import List, Dict, Any
import yaml
from pathlib import Path


class PromptBuilder:
    """Builds prompts from config and state."""
    
    # Cache for language templates
    _lang_templates: Dict[str, Dict[str, Any]] = None
    
    def __init__(self, state: "State", plan: "Plan", tasks: Dict[str, "TaskDefinition"],
                 tone: List[str], tone_definitions: Dict[str, str], 
                 guardrails: str, conversation_history: List[Dict[str, str]],
                 language: str = "en", completed_tasks: List[str] = None):
        self.state = state
        self.plan = plan
        self.tasks = tasks
        self.tone = tone
        self.tone_definitions = tone_definitions
        self.guardrails = guardrails
        self.conversation_history = conversation_history
        self.language = language
        self.completed_tasks = completed_tasks or []
        
        # Load language templates on first use
        if PromptBuilder._lang_templates is None:
            PromptBuilder._load_language_templates()
    
    @classmethod
    def _load_language_templates(cls):
        """Load language templates from YAML."""
        template_path = Path(__file__).parent.parent / "core" / "core_prompt.yaml"
        with open(template_path, 'r', encoding='utf-8') as f:
            cls._lang_templates = yaml.safe_load(f)
    
    def _get_lang(self, key: str, default: str = "") -> str:
        """Get language-specific text, fallback to English."""
        lang_data = self._lang_templates.get(self.language, self._lang_templates.get("en", {}))
        return lang_data.get(key, default)
    
    def build(self) -> str:
        """Build complete prompt with language support."""
        current_tasks = self.plan.get_current_block()
        
        return f'''{self._get_lang("language_instruction", "Speak naturally.")}

{self._get_lang("chat_history_header", "CONVERSATION HISTORY:")}
{self._format_history()}

{self._get_lang("current_state_header", "CURRENT STATE:")}
{self._format_state()}

{self._get_lang("guardrails_header", "GUARDRAILS:")}
{self.guardrails}

{self._get_lang("current_tasks_header", "CURRENT TASKS:")}
{self._format_tasks(current_tasks)}

{self._get_lang("tone_header", "TONE:")}
{self._format_tone()}

{self._get_lang("output_format_header", "OUTPUT FORMAT:")}
Respond with JSON matching this schema:
{{
  "assistant_reply": "Your natural response to the user",
  "task_results": [
    {{
      "task_id": "task_name",
      "key": "state_variable_name",
      "value": "extracted_value"
    }}
  ],
  "tools": [
    {{
      "tool": "tool_id",
      "options": ["option1", "option2"]  // if tool needs options
    }}
  ]
}}

CRITICAL RULES:
1. Respond naturally in assistant_reply
2. Each task_result extracts ONE piece of data: task_id, key (state variable), value
3. Only include tools if explicitly defined in current task
4. STRICTLY follow the tone guidelines above - they define how you should speak
5. If tone says "excited" or "exclamation marks", you MUST use them!

==============================================================================='''.strip()
    
    def _format_history(self) -> str:
        """Format conversation history."""
        if not self.conversation_history:
            return self._get_lang("none", "(No messages yet)")
        
        lines = []
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def _format_state(self) -> str:
        """Format current state."""
        state_dict = self.state.to_dict()
        if not state_dict:
            return self._get_lang("none", "(Empty)")
        
        lines = []
        for key, value in state_dict.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def _format_tasks(self, task_ids: List[str]) -> str:
        """Format task list with descriptions and tools."""
        if not task_ids:
            return self._get_lang("none", "(None)")
        
        lines = []
        for task_id in task_ids:
            task = self.tasks.get(task_id)
            if not task:
                continue
            
            # Skip completed tasks
            if task_id in self.completed_tasks:
                continue
            
            lines.append(f"\nTask: {task_id}")
            lines.append(f"Description: {task.description}")
            
            if task.expects:
                lines.append(f"Expected to collect: {', '.join(task.expects)}")
            
            if task.tools:
                lines.append("Available tools:")
                for tool_def in task.tools:
                    tool_id = tool_def.get("tool", "unknown")
                    lines.append(f"  - {tool_id}")
        
        return "\n".join(lines)
    
    def _format_tone(self) -> str:
        """Format active tones."""
        if not self.tone:
            return "Natural and helpful"
        
        descriptions = []
        for tone_id in self.tone:
            desc = self.tone_definitions.get(tone_id, tone_id)
            descriptions.append(desc)
        
        return " ".join(descriptions)
