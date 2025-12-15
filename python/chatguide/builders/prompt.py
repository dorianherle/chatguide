from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path
from ..core.task import Task


# ============================================================
# Prompt View (UNCHANGED)
# ============================================================

@dataclass
class PromptView:
    """View model for prompt generation."""
    current_task: Optional[Task]
    pending_tasks: List[Task]
    completed_tasks: List[str]
    state: Dict[str, Any]
    tone_text: str
    guardrails: str
    history: List[Dict[str, str]]
    language: str = "en"
    next_block_task: Optional[Task] = None  # First task of next block
    recent_extractions: List[Dict[str, Any]] = None  # Last N extractions for corrections


# ============================================================
# Prompt Builder (REFACTORED)
# ============================================================

class PromptBuilder:
    """Builds a clean, structured prompt from config and state."""

    _lang_templates: Dict[str, Dict[str, Any]] = None

    def __init__(self, view: PromptView):
        self.view = view
        if PromptBuilder._lang_templates is None:
            self._load_language_templates()

    # --------------------------------------------------
    # Language templates
    # --------------------------------------------------

    @classmethod
    def _load_language_templates(cls):
        template_path = Path(__file__).parent.parent / "core" / "core_prompt.yaml"
        with open(template_path, "r", encoding="utf-8") as f:
            cls._lang_templates = yaml.safe_load(f)

    def _get_lang(self, key: str, default: str = "") -> str:
        lang_data = self._lang_templates.get(
            self.view.language,
            self._lang_templates.get("en", {})
        )
        return lang_data.get(key, default)

    # --------------------------------------------------
    # Public entry point
    # --------------------------------------------------

    def build(self) -> str:
        sections = [
            self._system_role(),
            self._context_section(),
            self._objective_section(),
            self._response_contract(),
        ]
        return "\n\n".join(s for s in sections if s).strip()

    # ==================================================
    # Prompt sections
    # ==================================================

    def _system_role(self) -> str:
        return self._get_lang(
            "language_instruction",
            "You are a helpful assistant. Speak naturally."
        )

    def _context_section(self) -> str:
        return f"""
CONTEXT
-------
Conversation history:
{self._format_history()}

Known facts (verified — do NOT re-ask):
{self._format_state()}

Recent extractions (last values captured — user may correct these):
{self._format_recent_extractions()}
""".strip()

    def _objective_section(self) -> str:
        return f"""
OBJECTIVE
---------
Current task:
{self._format_current_task()}

Next task (after completion):
{self._format_next_task()}

Tone:
{self.view.tone_text}

Output Format:
- task_results: put here all extracted/corrected values from the user's response. If a key already exists in state, overwrite it. Include both new extractions and corrections to recent values.
- tools: if the task requires the use of a tool, add the tool id and options to the tools key.
General:
- After completing the current task, smoothly transition to the next task in the same reply.
""".strip()

    def _response_contract(self) -> str:
        # Get expected keys for current task
        current_task = self.view.current_task
        expected_keys = []
        if current_task and current_task.expects:
            expected_keys = [exp.key for exp in current_task.expects]

        expected_keys_str = ", ".join(f'"{k}"' for k in expected_keys) if expected_keys else "none"

        return f"""
RESPONSE FORMAT
---------------
Respond ONLY with valid JSON:

{{
  "assistant_reply": "Natural response shown to the user",
  "task_results": [
    {{
      "task_id": "task_name",
      "key": "state_variable_name",
      "value": "extracted_value_or_null"
    }}
  ],
  "tools": []
}}

MANDATORY EXTRACTION RULES:
- Expected keys: {expected_keys_str}
- OUTPUT EXACTLY ONE task_result FOR EACH expected key (no more, no less)
- Use value: null if you cannot extract a meaningful value
- NO MISSING task_results entries - every expected key must be present
- NO EXTRA keys - only output keys listed in expected keys
- value can be null but key must be present in task_results

Constraints:
- assistant_reply: Natural conversational response to user
- task_results: One entry per expected key, value can be string or null
- tools: Leave empty array [] (tools not used in minimal v1)
""".strip()

    # ==================================================
    # Formatting helpers (largely preserved)
    # ==================================================

    def _format_history(self) -> str:
        if not self.view.history:
            return self._get_lang("none", "(No messages yet)")

        lines = []
        for msg in self.view.history[-10:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _format_state(self) -> str:
        if not self.view.state:
            return self._get_lang("none", "(Empty)")

        return "\n".join(
            f"- {key}: {value}"
            for key, value in self.view.state.items()
        )

    def _format_recent_extractions(self) -> str:
        extractions = self.view.recent_extractions or []
        if not extractions:
            return "(No recent extractions)"

        # Show last 10, most recent last
        last_10 = extractions[-10:]
        return "\n".join(
            f"- {e['key']}: {e['value']}"
            for e in last_10
        )

    def _format_current_task(self) -> str:
        task = self.view.current_task
        if not task:
            return "(no active task)"

        return f"- {task.id}: {task.description}"

    def _format_next_task(self) -> str:
        task = self.view.next_block_task
        if not task:
            return "(no further tasks)"

        return f"- {task.id}: {task.description}"

    def _format_tasks(self) -> str:
        """
        Kept for compatibility if other code still calls it.
        Not used directly in the new prompt layout.
        """
        if not self.view.pending_tasks:
            return self._get_lang("none", "(None)")

        lines = []
        current_task_id = self.view.current_task.id if self.view.current_task else None

        for task in self.view.pending_tasks:
            is_current = (task.id == current_task_id)
            prefix = "(current task)" if is_current else ""
            lines.append(f"Task: {task.id} {prefix}")
            lines.append(f"Description: {task.description}")

            if task.expects:
                expects = []
                for exp in task.expects:
                    if hasattr(exp, "key"):
                        expects.append(exp.key)
                    else:
                        expects.append(str(exp))
                lines.append(f"Expected to collect: {', '.join(expects)}")

            if task.tools:
                lines.append("Available tools:")
                for tool_def in task.tools:
                    lines.append(f"  - {tool_def.get('tool', 'unknown')}")

            lines.append("")

        return "\n".join(lines).strip()
