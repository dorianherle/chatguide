"""AuditLog - append-only change tracking."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: str
    key: str
    old_value: Any
    new_value: Any
    source_task: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditLog:
    """Append-only log of all state changes."""
    
    def __init__(self):
        self._entries: List[AuditEntry] = []
    
    def log(self, key: str, old_value: Any, new_value: Any, source_task: Optional[str] = None):
        """Log a state change."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            key=key,
            old_value=old_value,
            new_value=new_value,
            source_task=source_task
        )
        self._entries.append(entry)
    
    def search(
        self, 
        key: Optional[str] = None, 
        task: Optional[str] = None,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search audit log with filters.
        
        Args:
            key: Filter by state key
            task: Filter by source task
            since: Filter by timestamp (ISO format)
        
        Returns:
            List of matching audit entries
        """
        results = self._entries
        
        if key:
            results = [e for e in results if e.key == key]
        
        if task:
            results = [e for e in results if e.source_task == task]
        
        if since:
            results = [e for e in results if e.timestamp >= since]
        
        return [e.to_dict() for e in results]
    
    def get_latest(self, key: str) -> Optional[Dict[str, Any]]:
        """Get the most recent change for a key."""
        entries = [e for e in self._entries if e.key == key]
        if entries:
            return entries[-1].to_dict()
        return None
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Export all entries as list."""
        return [e.to_dict() for e in self._entries]
    
    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "AuditLog":
        """Restore audit log from list."""
        log = cls()
        for entry_data in data:
            log._entries.append(AuditEntry(**entry_data))
        return log
