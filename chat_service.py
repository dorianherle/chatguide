from chatguide import ChatGuide
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class ChatService:
    def __init__(self, debug: bool = False):
        self.guide = None
        self.debug = debug
        self.initialize_guide()
    
    def initialize_guide(self, language="en"):
        """Initialize a fresh ChatGuide instance with selected language"""
        self.guide = ChatGuide(debug=self.debug)
        self.guide.load_from_file("config.yaml")
        
        # Set chatbot name
        self.guide.set_chatbot_name("Sol")
        
        # Store selected language for memory
        self.selected_language = language
        
        self.guide.set_task_flow([
            # Phase 1: Basic Info
            ["get_name", "get_age"],
            ["get_origin", "get_location"],
            
            # Phase 2: Moving Details
            ["get_move_date", "get_move_reason"],
            ["get_move_choice"],
            
            # Phase 3: Language & Integration
            ["get_language_level", "get_language_comfort"],
            
            # Phase 4: Social Connections
            ["get_social_network", "get_family_location"],
            ["get_friends_origin"],
            
            # Phase 5: Emotional Assessment
            ["get_homesickness", "get_grief_intensity"],
            ["get_adaptation_level"],
            
            # Phase 6: Support & Goals
            ["get_biggest_challenge", "get_support_system"],
            ["get_stay_duration", "get_primary_goal"]
        ], persistent=["get_emotion", "detect_info_updates"])
        
        # Add language instruction to memory
        memory_base = "You are Sol, a warm and empathetic AI companion specialized in helping people navigate the emotional challenges of moving to a new country. You understand moving grief, cultural adaptation, and homesickness deeply."
        if language != "en":
            memory_base += f"\n\nIMPORTANT: The user has selected to communicate in their preferred language. You MUST respond ENTIRELY in the language code: {language}. ALL your responses, questions, and interactions should be in this language from the very first message."
        
        # Add instruction for first message
        memory_base += "\n\nFor your first message: Introduce yourself as Sol, welcome the user warmly, and tell them you're here to help them navigate their journey of moving to a new place. Keep it friendly, upbeat, and use emojis!"
        
        self.guide.start_conversation(
            memory=memory_base,
            starting_message="",  # Let the model generate the first message
            tones=["neutral"]
        )
    
    def get_starting_message(self):
        """Get the initial message"""
        return "Hey there! 👋 I'm Sol, and I'm here to help you navigate this whole 'moving to a new place' adventure. Ready to get started? (Fair warning: I might ask you some questions, but I promise to keep it fun! 😄)"
    
    def send_message(self, user_input):
        """Send user message and get AI response, also return the exact prompt used."""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")
        
        # Add user message to history
        self.guide.add_user_message(user_input)
        
        # Capture the exact prompt that will be sent
        outgoing_prompt = self.guide.prompt()

        # Get AI response
        reply = self.guide.chat(
            model="gemini/gemini-2.5-flash-lite", 
            api_key=GEMINI_API_KEY
        )
        
        return reply, outgoing_prompt
    
    def get_debug_info(self):
        """Get debug information"""
        return self.guide.get_debug_info()
    
    def reset(self, language="en"):
        """Reset the chat service with optional language selection"""
        self.initialize_guide(language)
    
    def is_api_key_set(self):
        """Check if API key is configured"""
        return bool(GEMINI_API_KEY)

