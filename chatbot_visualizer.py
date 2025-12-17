import streamlit as st
import json
import os
import yaml
from google import genai
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Enable chat input widget
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize Colorama
init(autoreset=True)

# Load environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY")

# --- Configuration & State ---

class StateManager:
    def __init__(self, schema_path="data_schema.yaml"):
        with open(schema_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.persona = self.config.get('system_persona', "You are a helpful assistant.")
        self.blocks = self.config.get('blocks', [])
        self.current_block_index = 0
        self.extracted_data = {}
        self.history = [] # List of {"role": str, "content": str}
        self.current_turn_in_block = 0
        self.turns_threshold = 5  # Default turns before audit

    def get_current_block(self):
        if self.current_block_index < len(self.blocks):
            return self.blocks[self.current_block_index]
        return None

    def get_missing_fields_in_block(self):
        block = self.get_current_block()
        if not block:
            return []

        missing = []
        for field in block['fields']:
            if field['key'] not in self.extracted_data:
                missing.append(field)
        return missing

    def update_data(self, new_data):
        """Updates extracted data and advances block if current is full."""
        if not new_data:
            return

        for k, v in new_data.items():
            if v and v != "null":
                self.extracted_data[k] = v

        # Check if we should advance block
        missing = self.get_missing_fields_in_block()
        if not missing:
            if self.current_block_index < len(self.blocks):
                self.current_block_index += 1
                self.current_turn_in_block = 0

    def is_complete(self):
        return self.current_block_index >= len(self.blocks)

    def increment_turn(self):
        self.current_turn_in_block += 1

    def should_audit(self):
        return self.current_turn_in_block >= self.turns_threshold

    def reset_turn_counter(self):
        self.current_turn_in_block = 0

# --- LLM Wrappers ---

class SidecarDirector:
    """
    The 'Manager'. Checks progress, extracts data, and directs the actor.
    """
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = model_name

    def analyze(self, state_manager, last_user_input):
        current_block = state_manager.get_current_block()
        missing = state_manager.get_missing_fields_in_block()

        # We ask the Sidecar to do two things:
        # 1. Extract JSON data from the last turn.
        # 2. Give a hidden instruction to the chatbot.

        prompt = f"""
        You are the Director of a roleplay.

        CONTEXT:
        Current Goal Block: {current_block['description'] if current_block else 'Conversation Finished'}
        Fields needed in this block: {[f['key'] for f in missing]}
        Current Extracted Data: {json.dumps(state_manager.extracted_data)}
        Last User Input: "{last_user_input}"

        TASK:
        1. Extract any values for the fields needed from the user input. Return as JSON.
        2. Create a 'Stage Direction' for the Actor LLM.
           - If data is missing, tell the Actor to guide the user there naturally.
           - If the block is finished, tell the Actor to transition to the next topic.
           - If the user is off-topic, tell the Actor to entertain it briefly then pivot back.

        OUTPUT FORMAT (JSON ONLY):
        {{
            "extracted": {{ "key": "value" }},
            "stage_direction": "Instruction for the main LLM"
        }}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"temperature": 0.2, "max_output_tokens": 512}
            )
            # Simple cleaning to ensure JSON
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            return {"extracted": {}, "stage_direction": "Continue the conversation naturally."}

class MainActor:
    """
    The 'Talent'. Converses with the user based on instructions.
    """
    def __init__(self, model_name="gemini-2.5-flash-lite"):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = model_name

    def generate_response(self, state_manager, stage_direction, user_input):
        # Construct the context

        system_instruction = f"""
        SYSTEM INSTRUCTIONS:
        Persona: {state_manager.persona}

        CURRENT OBJECTIVE (Hidden from user):
        {stage_direction}

        CONSTRAINTS:
        - Do NOT explicitly say "I need to extract [field]".
        - Be natural. Make it flow.
        - Keep the extracted data in mind: {json.dumps(state_manager.extracted_data)}
        """

        # Build chat history for Gemini
        chat_history = []
        for msg in state_manager.history:
            role = "user" if msg['role'] == "user" else "model"
            chat_history.append({"role": role, "parts": [msg['content']]})

        # Add current turn manually to the prompt context (or append to history)
        # Using a stateless generation approach here for total control over system prompt
        full_prompt = f"{system_instruction}\n\nCHAT HISTORY:\n{chat_history}\n\nUSER: {user_input}\nYOU:"

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config={"temperature": 0.7, "max_output_tokens": 512}
        )
        return response.text

# --- Streamlit Interface ---

def main():
    st.title("🤖 Gearbox Chatbot - Visual Test Interface")

    # Initialize session state
    if 'state_manager' not in st.session_state:
        st.session_state.state_manager = StateManager()
        st.session_state.director = SidecarDirector()
        st.session_state.actor = MainActor()
        st.session_state.director_logs = []
        st.session_state.audit_triggered = False
        st.session_state.conversation_started = False

    state = st.session_state.state_manager
    director = st.session_state.director
    actor = st.session_state.actor

    # Layout: Chat (left) and Engine Room (right)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("💬 Conversation")

        # Display chat messages using Streamlit's chat interface
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Start conversation if not started
        if not st.session_state.conversation_started and not state.is_complete():
            # Initial greeting from bot
            initial_direction = "Greet the user warmly and ask for their name, age, and where they are from to start building their profile."
            initial_response = actor.generate_response(state, initial_direction, "")

            with st.chat_message("assistant"):
                st.markdown(initial_response)

            st.session_state.messages.append({"role": "assistant", "content": initial_response})
            state.history.append({"role": "assistant", "content": initial_response})
            st.session_state.conversation_started = True

        # Chat input
        if not state.is_complete():
            if prompt := st.chat_input("Type your message..."):
                # Add user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                # Increment turn counter
                state.increment_turn()

                # Check if audit should trigger
                if state.should_audit():
                    st.session_state.audit_triggered = True
                    # Run Sidecar Analysis
                    analysis = director.analyze(state, prompt)

                    # Update State
                    state.update_data(analysis.get("extracted", {}))
                    new_direction = analysis.get("stage_direction", "Continue conversation.")

                    # Log director's thoughts
                    log_entry = f"Audit triggered at turn {state.current_turn_in_block}. Extracted: {analysis.get('extracted', {})}. Direction: {new_direction}"
                    st.session_state.director_logs.append(log_entry)

                    # Reset turn counter after audit
                    state.reset_turn_counter()
                else:
                    new_direction = "Continue the natural conversation flow."
                    st.session_state.audit_triggered = False

                # Generate Actor response
                response = actor.generate_response(state, new_direction, prompt)

                # Add assistant message
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

                # Update history
                state.history.append({"role": "user", "content": prompt})
                state.history.append({"role": "assistant", "content": response})

                st.rerun()
        else:
            st.success("🎉 All data extracted! Conversation complete.")
            if st.button("Start New Conversation"):
                st.session_state.clear()
                st.rerun()

    with col2:
        st.subheader("⚙️ Engine Room")

        # Progress Bar
        current_turn = state.current_turn_in_block
        threshold = state.turns_threshold
        progress = min(current_turn / threshold, 1.0)

        st.progress(progress)
        if current_turn < threshold:
            st.caption(f"Turn {current_turn} of {threshold} (until next Audit)")
        else:
            st.caption(f"🔍 Audit triggered! Processing...")

        # Live State (only updates after audit)
        st.subheader("📊 Live State")
        if st.session_state.audit_triggered or state.is_complete():
            st.json(state.extracted_data)
        else:
            st.caption("State updates after each audit cycle")

        # Director's Log
        st.subheader("🎭 Director's Log")
        log_container = st.container(height=200)
        with log_container:
            for log in st.session_state.director_logs[-10:]:  # Show last 10 entries
                st.code(log, language=None)

        # Current Block Info
        st.subheader("📋 Current Block")
        current_block = state.get_current_block()
        if current_block:
            st.write(f"**{current_block['description']}**")
            missing = state.get_missing_fields_in_block()
            if missing:
                st.write("Missing fields:")
                for field in missing:
                    st.write(f"- {field['key']}")
            else:
                st.success("Block complete!")
        else:
            st.success("All blocks complete!")

        # Prompt Display
        with st.expander("🔍 Latest Prompts", expanded=False):
            if st.session_state.messages:
                latest_user_msg = ""
                for msg in reversed(st.session_state.messages):
                    if msg["role"] == "user":
                        latest_user_msg = msg["content"]
                        break

                if latest_user_msg:
                    st.subheader("🎭 Director Prompt")
                    current_block = state.get_current_block()
                    missing = state.get_missing_fields_in_block()
                    director_prompt = f"""
You are the Director of a roleplay.

CONTEXT:
Current Goal Block: {current_block['description'] if current_block else 'Conversation Finished'}
Fields needed in this block: {[f['key'] for f in missing]}
Current Extracted Data: {json.dumps(state.extracted_data)}
Last User Input: "{latest_user_msg}"

TASK:
1. Extract any values for the fields needed from the user input. Return as JSON.
2. Create a 'Stage Direction' for the Actor LLM.
   - If data is missing, tell the Actor to guide the user there naturally.
   - If the block is finished, tell the Actor to transition to the next topic.
   - If the user is off-topic, tell the Actor to entertain it briefly then pivot back.

OUTPUT FORMAT (JSON ONLY):
{{
    "extracted": {{ "key": "value" }},
    "stage_direction": "Instruction for the main LLM"
}}
"""
                    st.code(director_prompt, language="text")

                    # Show latest actor prompt if available
                    if len(st.session_state.messages) >= 2:
                        latest_direction = "Continue the natural conversation flow."  # Default
                        if st.session_state.director_logs:
                            latest_log = st.session_state.director_logs[-1]
                            # Extract direction from log
                            if "Direction:" in latest_log:
                                latest_direction = latest_log.split("Direction: ")[-1]

                        st.subheader("🎬 Actor Prompt")
                        actor_prompt = f"""
SYSTEM INSTRUCTIONS:
Persona: {state.persona}

CURRENT OBJECTIVE (Hidden from user):
{latest_direction}

CONSTRAINTS:
- Do NOT explicitly say "I need to extract [field]".
- Be natural. Make it flow.
- Keep the extracted data in mind: {json.dumps(state.extracted_data)}

CHAT HISTORY:
{json.dumps(state.history[-4:])}

USER: {latest_user_msg}
YOU:
"""
                        st.code(actor_prompt, language="text")

        # Debug Info
        with st.expander("🔧 Debug Info"):
            st.write(f"Current Block Index: {state.current_block_index}")
            st.write(f"Total Blocks: {len(state.blocks)}")
            st.write(f"Turn Counter: {current_turn}")
            st.write(f"Conversation Started: {st.session_state.conversation_started}")

if __name__ == "__main__":
    main()
