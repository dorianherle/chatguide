### Prompt Conversation LLM ###


def get_prompt_conversation_llm(persona: str, conversation:str, mandate: str) -> str:
    return f"""
Persona
{persona}
Conversation so far:
{conversation}
Mandate
{mandate}

Be clever. Don't directly ask the user all questions in the mandate. You can take multiple turns to ask the questions in the mandate.
I mean be socially smart, look at the conversation so far and the mandate and come up with a natural conversation flow.
"""

### Prompt Sidecar Director ###
def get_prompt_sidecar_director(conversation: str, current_extraction_block, next_extraction_block) -> str:
    # Format the current fields
    def format_current_fields(fields):
        if isinstance(fields, list):
            formatted_lines = []
            for field in fields:
                if isinstance(field, dict):
                    name = field.get('name', 'Unknown')
                    question = field.get('question', 'No question')
                    validation = field.get('validation', '')
                    if validation and validation != 'No validation':
                        formatted_lines.append(f"- {name}: {question} (must be {validation})")
                    else:
                        formatted_lines.append(f"- {name}: {question}")
                else:
                    formatted_lines.append(f"- {field}")
            return '\n'.join(formatted_lines)
        return fields

    # Format the next fields
    def format_next_fields(fields):
        if isinstance(fields, list):
            formatted_lines = []
            for field in fields:
                if isinstance(field, dict):
                    name = field.get('name', 'Unknown')
                    question = field.get('question', 'No question')
                    formatted_lines.append(f"- {name}: {question}")
                else:
                    formatted_lines.append(f"- {field}")
            return '\n'.join(formatted_lines)
        return fields

    formatted_current_fields = format_current_fields(current_extraction_block)
    formatted_next_fields = format_next_fields(next_extraction_block)

    return f"""You are the Director of a roleplay.

Your job has TWO STRICTLY SEPARATED responsibilities.

----------------------------------------
1) EXTRACTION (CURRENT BLOCK ONLY)
----------------------------------------

Below is the CURRENT EXTRACTION BLOCK.
You may extract values ONLY for the fields listed here.

CURRENT EXTRACTION BLOCK FIELDS:
{formatted_current_fields}

Rules:
- Extract ONLY values explicitly stated in the conversation.
- Do NOT infer, assume, normalize, or guess.
- If a field is not explicitly mentioned, DO NOT include it.
- If none of the fields are mentioned, return an empty object {{}}.
- NEVER extract fields that are not listed in the CURRENT EXTRACTION BLOCK.

Return extracted values under the key "extracted".

----------------------------------------
2) STAGE DIRECTION (CONDITIONAL)
----------------------------------------

You must generate ONE stage direction for the conversation LLM.

Step 1 — Check CURRENT BLOCK completeness:
- If one or more fields from the CURRENT EXTRACTION BLOCK are missing or unclear:
  -> The stage direction MUST guide the bot to naturally elicit ONLY those missing fields.

Step 2 — If and ONLY IF the CURRENT BLOCK is fully complete:
- Shift the stage direction toward the NEXT EXTRACTION BLOCK below.
- Do NOT extract these fields yet.
- The goal is to naturally encourage the user to mention them next.

NEXT EXTRACTION BLOCK FIELDS:
{formatted_next_fields}

Rules for stage direction:
- Do NOT use a checklist or interrogation style.
- Be conversational and natural.
- Instructions must be directed at the Bot.
- Instructions MUST start with: "You need to..."

Return the instruction under the key "stage_direction".

----------------------------------------
CONVERSATION:
{conversation}

----------------------------------------
OUTPUT FORMAT (JSON ONLY):
{{
  "extracted": {{}},
  "stage_direction": "..."
}}"""