from chatguide import ChatGuide
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class ChatService:
    def __init__(self):
        self.guide = None
        self.initialize_guide()
    
    def initialize_guide(self):
        """Initialize a fresh ChatGuide instance"""
        self.guide = ChatGuide()
        self.guide.load_from_file("config.yaml")
        self.guide.set_task_flow([
            ["get_name", "get_origin"],
            ["offer_language", "get_location"],
            ["reflect", "suggest"]
        ], persistent=["get_emotion"])
        
        self.guide.start_conversation(
            memory="You are Sol. You are a friendly and helpful assistant.",
            starting_message="Hi there! My name is Sol. Tell me are you ready for a really really hard question? ;)",
            tones=["neutral"]
        )
    
    def get_starting_message(self):
        """Get the initial message"""
        return "Hi there! My name is Sol. Tell me are you ready for a really really hard question? ;)"
    
    def send_message(self, user_input):
        """Send user message and get AI response, also return the exact prompt used."""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")
        
        # Update guide state
        self.guide.chat_history += f"\nUser: {user_input}"
        
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
        return {
            "current_tasks": self.guide.get_current_tasks(),
            "next_tasks": self.guide.get_next_tasks(),
            "completed_tasks": [k for k, v in self.guide.completed_tasks.items() if v],
            "active_tones": self.guide.tones_active,
            "turn_count": self.guide.turn_count,
            "batch_index": self.guide.current_batch_idx,
            "all_done": self.guide.all_done()
        }
    
    def reset(self):
        """Reset the chat service"""
        self.initialize_guide()
    
    def is_api_key_set(self):
        """Check if API key is configured"""
        return bool(GEMINI_API_KEY)
