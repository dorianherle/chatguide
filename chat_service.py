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
    
    def initialize_guide(self):
        """Initialize a fresh ChatGuide instance"""
        self.guide = ChatGuide(debug=self.debug)
        self.guide.load_from_file("config.yaml")
        
        # Set chatbot name
        self.guide.set_chatbot_name("Sol")
        
        self.guide.set_task_flow([
            # Phase 1: Basic Info
            ["get_name", "get_age"],
            ["get_origin", "offer_language"],
            ["get_location"],
            
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
        
        self.guide.start_conversation(
            memory="You are Sol, a warm and empathetic AI companion specialized in helping people navigate the emotional challenges of moving to a new country. You understand moving grief, cultural adaptation, and homesickness deeply.",
            starting_message="Hey there! 👋 I'm Sol, and I'm here to help you navigate this whole 'moving to a new place' adventure. Ready to get started? (Fair warning: I might ask you some questions, but I promise to keep it fun! 😄)",
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
    
    def reset(self):
        """Reset the chat service"""
        self.initialize_guide()
    
    def is_api_key_set(self):
        """Check if API key is configured"""
        return bool(GEMINI_API_KEY)

