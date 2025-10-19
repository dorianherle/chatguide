"""ChatService - wrapper for ChatGuide with language support."""

import os
from pathlib import Path
from dotenv import load_dotenv
from chatguide import ChatGuide

load_dotenv()


class ChatService:
    """Wrapper with language-aware initialization."""
    
    def __init__(self, debug: bool = False):
        self.guide = ChatGuide(debug=debug)
        self.debug = debug
    
    def initialize_guide(self, language: str = "en"):
        """Load config and start conversation."""
        # Load config
        config_path = Path(__file__).parent / "config.yaml"
        self.guide.load_config(str(config_path))
        
        # Set language (this will affect the entire prompt)
        self.guide.set_language(language)
        
        # Language names (for intro task substitution)
        language_names = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean"
        }
        
        language_name = language_names.get(language, "English")
        
        # Format intro task with language
        intro_task = self.guide.config.tasks.get("introduce_yourself")
        if intro_task:
            intro_task.description = intro_task.description.replace("{language}", language_name)
        
        # Set chatbot name
        self.guide.state.participants.chatbot = "Sol"
        
        # Set flow - progressive understanding of the user's journey
        self.guide.set_flow(
            batches=[
                ["introduce_yourself"],                                    # Playful intro
                ["get_name", "get_age", "get_origin"],                    # Who are you?
                ["get_location","get_move_date"],
                ["get_move_reason", "get_move_choice"],  # The move story
                ["get_language_level"],                   # Where & how now
                ["get_social_network", "get_adaptation_level"],            # Connections
                ["get_family_location"],                  # How feeling
                ["get_biggest_challenge", "get_support_system"],          # Deeper dive
                ["get_stay_duration", "get_primary_goal"],                # Future plans
            ],
            persistent=["get_emotion", "detect_info_updates"]
        )
        
        # Start
        memory = "You are Sol, a friendly AI helping people who moved to a new country."
        self.guide.start(memory=memory, tones=["neutral"])
    
    def send_message(self, user_input: str):
        """Send user message and get reply."""
        self.guide.add_user_message(user_input)
        outgoing_prompt = self.guide.get_prompt()
        api_key = os.getenv("GEMINI_API_KEY")
        reply = self.guide.chat(
            model="gemini/gemini-2.5-flash-lite", 
            api_key=api_key
            # max_tokens defaults to 4000
        )
        return reply, outgoing_prompt
    
    def get_debug_info(self):
        """Get debug info."""
        return self.guide.get_state()
