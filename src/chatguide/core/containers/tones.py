"""Tones container - manages active tones."""

from typing import List


class Tones:
    """Tracks active tones.
    
    All attributes are directly editable:
        tones.active = ["friendly", "playful"]
        tones.active.append("urgent")
    """
    
    def __init__(self):
        self.active: List[str] = ["neutral"]
    
    def set_tones(self, tones: List[str]):
        """Replace active tones (convenience method)."""
        self.active = tones
    
    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "active": self.active.copy()
        }

