import json

### Prompt Conversation LLM ###

def get_prompt_conversation_llm(persona: str, conversation: str, mandate: str) -> str:
    """
    Generate prompt for the conversation LLM that maintains natural dialogue
    while extracting required information.
    """
    
    return f"""You are a conversational AI that needs to collect specific information from the user.

PERSONA:
{persona}

BEHAVIORAL RULES:
1. Match the user's communication style (casual/formal, brief/detailed, energetic/calm)
2. Ask ONLY ONE question at a time
3. Be direct - ask for what you need without over-explaining
4. If user shows frustration ("stop", "dude", etc.), acknowledge and ask if they want to continue
5. CRITICAL: Only ask about fields in the "REQUIRED FIELDS" section below
6. Do NOT ask conversational follow-ups that aren't in the required fields

CONVERSATION HISTORY:
{conversation}

REQUIRED FIELDS TO COLLECT:
{mandate}

TASK:
Determine if ALL required fields have been explicitly provided by the user.
- Check each field in the "REQUIRED FIELDS" list
- A field is "collected" ONLY if the user explicitly stated it in plain language
- Do NOT infer from context, tone, or implicit information
- Do NOT mark fields as collected if they were only implied

If information is still missing:
- Generate your next response to collect the FIRST missing field
- Keep it natural and conversational
- Match the user's energy level

If ALL required fields have been collected:
- Set got_all_information to true
- Leave response empty

OUTPUT FORMAT (JSON ONLY):
{{
    "got_all_information": true|false,
    "response": "Your next message to the user (empty string if got_all_information is true)"
}}
"""


def get_prompt_sidecar_director(conversation: str, known_values: dict, to_extract) -> str:
    """
    Generate prompt for the sidecar director LLM that extracts structured data
    from the conversation without making inferences.
    """
    
    def format_fields(fields):
        """Format fields for display in the prompt"""
        if isinstance(fields, dict):
            return json.dumps(fields, indent=2)
        elif isinstance(fields, list):
            return "\n".join(f"- {json.dumps(f)}" for f in fields)
        return str(fields)

    return f"""You are a precise data extraction system. Your job is to identify what information has been explicitly stated by the user.

CONVERSATION TRANSCRIPT:
{conversation}

----------------------------------------
ALREADY EXTRACTED (don't re-extract these):
{json.dumps(known_values, indent=2)}

----------------------------------------
FIELDS YOU NEED TO EXTRACT:
{format_fields(to_extract)}

----------------------------------------
EXTRACTION RULES:
1. Extract ONLY information that was explicitly stated by the user
2. Do NOT infer, guess, or assume based on context
3. Do NOT extract information from the bot's messages, only the user's
4. If a field asks for specific data (name, age, country), extract ONLY that data type
5. For validation (like age 1-120), apply it during extraction
6. If data doesn't match the expected format, mark the field as missing

EXAMPLES:
- Field: get_name (extract user's name)
  User: "I'm Sarah" → Extract: {{"get_name": "Sarah"}}
  User: "Call me 123" → Missing (not a valid name)
  
- Field: get_age (extract age 1-120)  
  User: "I'm 25" → Extract: {{"get_age": 25}}
  User: "I'm 150" → Missing (unrealistic, ask for confirmation)

- Field: introduce_yourself (bot action, not user data)
  This is an INSTRUCTION for the bot, not data to extract → Skip entirely

----------------------------------------
YOUR TASK:

1. EXTRACTED: Which fields from the "FIELDS YOU NEED TO EXTRACT" list were explicitly provided by the user in the conversation?
   - Return as: {{"field_name": "value"}}
   - Only include NEW extractions (not already in ALREADY EXTRACTED)
   - Return empty dict {{}} if nothing new was extracted

2. MISSING: Which fields are still needed?
   - Return as: {{"field_name": "description"}}
   - Include ALL fields that haven't been extracted yet
   - EXCLUDE any "introduce_yourself" or bot instruction fields

OUTPUT (JSON ONLY - no other text):
{{
  "extracted": {{}},
  "missing": {{}}
}}
"""