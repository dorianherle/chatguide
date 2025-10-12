"""Participants container - chatbot and user names."""


class Participants:
    """Participant names.
    
    All attributes are directly editable:
        participants.chatbot = "Dr. Smith"
        participants.user = "Alice"
    """
    
    def __init__(self):
        self.chatbot: str = "Assistant"
        self.user: str = "Human"
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "chatbot": self.chatbot,
            "user": self.user
        }
