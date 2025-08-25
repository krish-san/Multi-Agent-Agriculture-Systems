"""
Local Storage System for Multi-Agent Agriculture Demo
Replaces Redis with file-based storage for single-user demo
"""

import os
import json
import pickle
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalStorage:
    """Local file-based storage for demo purposes"""
    
    def __init__(self, storage_dir: str = "data/local_cache"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.session_file = self.storage_dir / "sessions.json"
        self.cache_file = self.storage_dir / "cache.json"
        self.workflow_file = self.storage_dir / "workflows.pkl"
        
        logger.info(f"Local storage initialized at {self.storage_dir}")
    
    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration"""
        try:
            # Load existing cache
            cache = self._load_cache()
            
            # Set value with expiration if specified
            entry = {
                "value": value,
                "created": datetime.now().isoformat()
            }
            
            if expire_seconds:
                entry["expires"] = (datetime.now() + timedelta(seconds=expire_seconds)).isoformat()
            
            cache[key] = entry
            
            # Save cache
            self._save_cache(cache)
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key"""
        try:
            cache = self._load_cache()
            
            if key not in cache:
                return default
            
            entry = cache[key]
            
            # Check expiration
            if "expires" in entry:
                expire_time = datetime.fromisoformat(entry["expires"])
                if datetime.now() > expire_time:
                    # Remove expired entry
                    del cache[key]
                    self._save_cache(cache)
                    return default
            
            return entry["value"]
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            cache = self._load_cache()
            
            if key in cache:
                del cache[key]
                self._save_cache(cache)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def ping(self) -> bool:
        """Test storage connectivity (always True for local storage)"""
        return True
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"Could not load cache file: {e}")
            return {}
    
    def _save_cache(self, cache: Dict[str, Any]) -> None:
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save cache file: {e}")
    
    def store_workflow_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """Store workflow state for persistence"""
        try:
            # Load existing workflows
            workflows = {}
            if self.workflow_file.exists():
                with open(self.workflow_file, 'rb') as f:
                    workflows = pickle.load(f)
            
            # Store state
            workflows[thread_id] = {
                "state": state,
                "updated": datetime.now().isoformat()
            }
            
            # Save workflows
            with open(self.workflow_file, 'wb') as f:
                pickle.dump(workflows, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing workflow state: {e}")
            return False
    
    def get_workflow_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow state"""
        try:
            if not self.workflow_file.exists():
                return None
            
            with open(self.workflow_file, 'rb') as f:
                workflows = pickle.load(f)
            
            if thread_id in workflows:
                return workflows[thread_id]["state"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting workflow state: {e}")
            return None


class LocalStorageAdapter:
    """Adapter to make LocalStorage behave like Redis for compatibility"""
    
    def __init__(self):
        self.storage = LocalStorage()
        logger.info("Local storage adapter initialized for demo")
    
    def ping(self) -> bool:
        return self.storage.ping()
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        return self.storage.set(key, value, ex)
    
    def get(self, key: str) -> Any:
        return self.storage.get(key)
    
    def delete(self, key: str) -> bool:
        return self.storage.delete(key)
    
    def exists(self, key: str) -> bool:
        return self.storage.get(key) is not None
    
    def flushdb(self) -> bool:
        """Clear all data (for testing)"""
        try:
            # Remove cache files
            if self.storage.cache_file.exists():
                self.storage.cache_file.unlink()
            if self.storage.workflow_file.exists():
                self.storage.workflow_file.unlink()
            
            logger.info("Local storage cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing local storage: {e}")
            return False


# Global instance for demo use
local_storage = LocalStorageAdapter()

def get_demo_storage():
    """Get the demo storage instance"""
    return local_storage


class MemoryCheckpointSaver:
    """Simple in-memory checkpoint saver for workflows"""
    
    def __init__(self):
        self.checkpoints = {}
        logger.info("Memory checkpoint saver initialized")
    
    def put(self, thread_id: str, checkpoint: Dict[str, Any]) -> None:
        """Store a checkpoint"""
        self.checkpoints[thread_id] = checkpoint
    
    def get(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get a checkpoint"""
        return self.checkpoints.get(thread_id)
    
    def list(self, thread_id: str) -> list:
        """List checkpoints for a thread"""
        if thread_id in self.checkpoints:
            return [self.checkpoints[thread_id]]
        return []


def get_demo_checkpoint_saver():
    """Get a simple checkpoint saver for demo"""
    return MemoryCheckpointSaver()


if __name__ == "__main__":
    # Test the local storage
    print("Testing Local Storage System...")
    
    storage = LocalStorage()
    
    # Test basic operations
    storage.set("test_key", {"farm": "demo_farm", "crop": "wheat"})
    result = storage.get("test_key")
    print(f"Retrieved: {result}")
    
    # Test expiration
    storage.set("temp_key", "temporary_value", expire_seconds=2)
    print(f"Temp value: {storage.get('temp_key')}")
    
    print("Local storage system working!")
