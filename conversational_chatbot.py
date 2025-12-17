#!/usr/bin/env python3
"""
Single-conversation chatbot with occasional sidecar supervision.

- ONE main conversational LLM
- ONE sidecar LLM that:
  - extracts data
  - refocuses prompt
  - advances blocks
"""

import os
import json
import yaml
from typing import Dict, List, Any
from dotenv import load_dotenv
from google import genai

# ---------------------------------------------------------------------
# ENV
# ---------------------------------------------------------------------

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY")

# ---------------------------------------------------------------------
# LLM CLIENT
# ---------------------------------------------------------------------

class Gemini:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)

    def call(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 512,
        model: str = "gemini-2.5-flash-lite",
    ) -> str:
        res = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        return res.text.strip()

# ---------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------

class ChatState:
    """
    Holds conversation + block state.
    No LLM logic here.
    """

    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)

        self.blocks = cfg["blocks"]
        self.system_prompt = cfg["system_prompt"]
        self.sidecar_prompt = cfg["sidecar_system_prompt"]

        self.block_index = 0
        self.turns_in_block = 0

        self.extracted_data: Dict[str, Any] = {}
        self.history: List[Dict[str, str]] = []

    # -----------------------------
    # Block helpers
    # -----------------------------

    @property
    def block(self) -> Dict[str, Any]:
        return self.blocks[self.block_index]

    def missing_required(self) -> List[str]:
        return [
            f["name"]
            for f in self.block["fields"]
            if f.get("required", False) and f["name"] not in self.extracted_data
        ]

    def all_field_names(self) -> List[str]:
        return [f["name"] for f in self.block["fields"]]

    def advance_block(self) -> bool:
        if self.block_index + 1 >= len(self.blocks):
            return False
        self.block_index += 1
        self.turns_in_block = 0
        return True

    # -----------------------------
    # Mutation
    # -----------------------------

    def add_turn(self, user: str, assistant: str):
        self.history.append({"user": user, "assistant": assistant})
        self.turns_in_block += 1

    # -----------------------------
    # Sidecar context
    # -----------------------------

    def sidecar_snapshot(self) -> Dict[str, Any]:
        return {
            "current_block": self.block["name"],
            "block_description": self.block["description"],
            "turns_in_block": self.turns_in_block,
            "turn_limit": self.block.get("turns_threshold", 5),
            "expected_fields": self.all_field_names(),
            "missing_required_fields": self.missing_required(),
            "extracted_data": self.extracted_data,
            "recent_conversation": self.history[-4:],
        }

# ---------------------------------------------------------------------
# CHATBOT
# ---------------------------------------------------------------------

class Chatbot:
    def __init__(self, config_path: str = "chatbot_config.yaml"):
        self.llm = Gemini()
        self.state = ChatState(config_path)

    # -----------------------------
    # Main conversation LLM
    # -----------------------------

    def conversation_reply(self, user_msg: str) -> str:
        block = self.state.block

        prompt = f"""
{self.state.system_prompt}

CURRENT PHASE:
{block["name"]} — {block["description"]}

The assistant should be natural, human, and conversational.
Do NOT mention data collection or blocks.

User: {user_msg}
Assistant:
"""
        return self.llm.call(prompt, temperature=0.8)

    # -----------------------------
    # Sidecar supervision
    # -----------------------------

    def maybe_run_sidecar(self):
        block = self.state.block
        threshold = block.get("turns_threshold", 5)

        if self.state.turns_in_block < threshold:
            return

        prompt = f"""
{self.state.sidecar_prompt}

You are supervising an ongoing conversation.

STATE (JSON):
{json.dumps(self.state.sidecar_snapshot(), indent=2)}

Your job:
1. Extract any newly discovered field values
2. Decide whether to refocus the conversation
3. Decide whether to advance to the next block

Return STRICT JSON ONLY:

{{
  "extracted": {{ "<field>": <value>, ... }},
  "action": "continue" | "refocus" | "advance",
  "new_system_prompt": string | null,
  "reason": string
}}
"""

        raw = self.llm.call(prompt, temperature=0.2)

        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            print("⚠️ Sidecar returned invalid JSON")
            return

        # 1. Merge extracted data
        extracted = decision.get("extracted", {})
        if extracted:
            self.state.extracted_data.update(extracted)
            print(f"\n📊 Extracted: {extracted}")

        # 2. Refocus prompt
        if decision["action"] == "refocus" and decision.get("new_system_prompt"):
            self.state.system_prompt = decision["new_system_prompt"]
            print("\n🎯 Sidecar refocused prompt")

        # 3. Advance block
        if decision["action"] == "advance":
            if self.state.advance_block():
                print(f"\n➡️ Moved to block: {self.state.block['name']}")
            else:
                print("\n⛔ Cannot advance block")

        # Reset turn counter after sidecar decision
        self.state.turns_in_block = 0

    # -----------------------------
    # Public API
    # -----------------------------

    def handle(self, user_msg: str) -> str:
        reply = self.conversation_reply(user_msg)
        self.state.add_turn(user_msg, reply)
        self.maybe_run_sidecar()
        return reply

    def status(self):
        return {
            "block": self.state.block["name"],
            "extracted": self.state.extracted_data,
            "missing_required": self.state.missing_required(),
        }

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

if __name__ == "__main__":
    bot = Chatbot()

    print("🤖 Single-Conversation Chatbot")
    print("Commands: quit | status\n")

    while True:
        user = input("You: ").strip()
        if user.lower() == "quit":
            break
        if user.lower() == "status":
            print(json.dumps(bot.status(), indent=2))
            continue

        answer = bot.handle(user)
        print(f"🤖 {answer}")
