"""Interaction container - tones and turn tracking."""

from typing import List


class Interaction:
    """Manages tones and turn count.
    
    All attributes are directly editable:
        interaction.tones = ["friendly", "playful"]
        interaction.tones.append("urgent")
        interaction.turn_count = 5
    """
    
    def __init__(self):
        self.tones: List[str] = ["neutral"]
        self.turn_count: int = 0
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "tones": self.tones.copy(),
            "turn_count": self.turn_count
        }
