"""Storage adapters for persisting conversation state."""

from typing import Dict, Any, Optional
import json


class StorageAdapter:
    """Base class for storage adapters."""
    
    def save(self, conversation_id: str, state_dict: Dict[str, Any]):
        """Save conversation state."""
        raise NotImplementedError
    
    def load(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state."""
        raise NotImplementedError
    
    def delete(self, conversation_id: str):
        """Delete conversation state."""
        raise NotImplementedError


class SupabaseStorage(StorageAdapter):
    """Store conversation state in Supabase.
    
    Usage:
        storage = SupabaseStorage(url, key, table="conversations")
        
        # Save
        storage.save("user_123", guide.get_state())
        
        # Load
        state_dict = storage.load("user_123")
        # Then restore state from dict
    """
    
    def __init__(self, supabase_url: str, supabase_key: str, table: str = "conversations"):
        """Initialize Supabase storage.
        
        Args:
            supabase_url: Your Supabase project URL
            supabase_key: Your Supabase anon/service key
            table: Table name for storing conversations
        """
        try:
            from supabase import create_client
            self.client = create_client(supabase_url, supabase_key)
            self.table = table
        except ImportError:
            raise ImportError("Supabase not installed. Run: pip install supabase")
    
    def save(self, conversation_id: str, state_dict: Dict[str, Any]):
        """Save conversation state to Supabase."""
        data = {
            "id": conversation_id,
            "state": json.dumps(state_dict),
            "updated_at": "now()"
        }
        
        # Upsert (insert or update)
        self.client.table(self.table).upsert(data).execute()
    
    def load(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from Supabase."""
        result = self.client.table(self.table).select("state").eq("id", conversation_id).execute()
        
        if result.data and len(result.data) > 0:
            return json.loads(result.data[0]["state"])
        return None
    
    def delete(self, conversation_id: str):
        """Delete conversation from Supabase."""
        self.client.table(self.table).delete().eq("id", conversation_id).execute()


class RedisStorage(StorageAdapter):
    """Store conversation state in Redis.
    
    Usage:
        storage = RedisStorage(host="localhost", port=6379)
        storage.save("user_123", guide.get_state())
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 key_prefix: str = "chatguide:"):
        """Initialize Redis storage."""
        try:
            import redis
            self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.key_prefix = key_prefix
        except ImportError:
            raise ImportError("Redis not installed. Run: pip install redis")
    
    def save(self, conversation_id: str, state_dict: Dict[str, Any]):
        """Save conversation state to Redis."""
        key = f"{self.key_prefix}{conversation_id}"
        self.client.set(key, json.dumps(state_dict))
    
    def load(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from Redis."""
        key = f"{self.key_prefix}{conversation_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def delete(self, conversation_id: str):
        """Delete conversation from Redis."""
        key = f"{self.key_prefix}{conversation_id}"
        self.client.delete(key)


class FileStorage(StorageAdapter):
    """Store conversation state in local JSON files.
    
    Usage:
        storage = FileStorage(directory="conversations")
        storage.save("user_123", guide.get_state())
    """
    
    def __init__(self, directory: str = "conversations"):
        """Initialize file storage."""
        from pathlib import Path
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True)
    
    def save(self, conversation_id: str, state_dict: Dict[str, Any]):
        """Save conversation state to file."""
        file_path = self.directory / f"{conversation_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
    
    def load(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation state from file."""
        file_path = self.directory / f"{conversation_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def delete(self, conversation_id: str):
        """Delete conversation file."""
        file_path = self.directory / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()

