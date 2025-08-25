
import os
import redis
from typing import Optional
# TODO: Fix Redis checkpoint import when package is properly installed
# from langgraph.checkpoint.redis import RedisSaver
import logging

# Import local storage for demo mode
try:
    from .local_storage import LocalStorageAdapter, get_demo_storage, get_demo_checkpoint_saver
except ImportError:
    from local_storage import LocalStorageAdapter, get_demo_storage, get_demo_checkpoint_saver

logger = logging.getLogger(__name__)


class RedisConfig:
    
    def __init__(self):
        # Check if we're in demo mode (default for single user)
        self.demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
        
        if self.demo_mode:
            logger.info("Running in DEMO MODE - using local storage instead of Redis")
            return
        
        # Redis configuration (only used if demo_mode is False)
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_password = os.getenv('REDIS_PASSWORD', None)
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_ssl = os.getenv('REDIS_SSL', 'false').lower() == 'true'
        
        # Connection pool settings
        self.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', 10))
        self.retry_on_timeout = True
        self.socket_timeout = 30.0
        self.socket_connect_timeout = 30.0
        
        logger.info(f"Redis config initialized - Host: {self.redis_host}:{self.redis_port}")
    
    def get_connection_params(self) -> dict:
        if self.demo_mode:
            return {}  # No connection params needed for local storage
        
        params = {
            'host': self.redis_host,
            'port': self.redis_port,
            'db': self.redis_db,
            'retry_on_timeout': self.retry_on_timeout,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'max_connections': self.max_connections,
            'decode_responses': True  # Important for LangChain compatibility
        }
        
        if self.redis_password:
            params['password'] = self.redis_password
        
        if self.redis_ssl:
            params['ssl'] = True
            params['ssl_cert_reqs'] = None  # For Redis Cloud
        
        return params


class RedisConnectionManager:
    
    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or RedisConfig()
        self._client = None
        self._saver = None
        
        if self.config.demo_mode:
            logger.info("Demo mode: Using local storage instead of Redis")
        else:
            logger.info("Production mode: Redis connection manager initialized")
    
    def get_client(self):
        if self._client is None:
            # Use local storage in demo mode
            if self.config.demo_mode:
                logger.info("Using local storage adapter for demo")
                self._client = get_demo_storage()
                return self._client
            
            # Original Redis logic for production
            try:
                connection_params = self.config.get_connection_params()
                self._client = redis.Redis(**connection_params)
                
                # Test the connection
                self._client.ping()
                logger.info("Redis client connected successfully")
                
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                # Fall back to local storage
                logger.warning("Using local storage fallback")
                self._client = get_demo_storage()
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {str(e)}")
                self._client = get_demo_storage()
        
        return self._client
    
    def get_saver(self):
        if self._saver is None:
            # Use memory saver in demo mode
            if self.config.demo_mode:
                logger.info("Using demo checkpoint saver")
                self._saver = get_demo_checkpoint_saver()
                return self._saver
            
            # Original Redis saver logic for production
            try:
                client = self.get_client()
                
                # Only create RedisSaver if we have a real Redis connection
                if hasattr(client, 'ping') and not hasattr(client, 'storage'):  # Real Redis client
                    try:
                        # Try to import and use RedisSaver
                        from langgraph.checkpoint.redis import RedisSaver
                        self._saver = RedisSaver(client)
                        logger.info("RedisSaver initialized successfully")
                    except ImportError:
                        logger.warning("RedisSaver not available, using memory fallback")
                        self._saver = get_demo_checkpoint_saver()
                else:
                    # Use demo saver as fallback
                    self._saver = get_demo_checkpoint_saver()
                    logger.warning("Using demo checkpoint saver")
                    
            except Exception as e:
                logger.error(f"Failed to initialize saver: {str(e)}")
                # Fallback to demo saver
                self._saver = get_demo_checkpoint_saver()
                logger.warning("Using demo checkpoint saver due to initialization failure")
        
        return self._saver
    
    def test_connection(self) -> bool:
        try:
            client = self.get_client()
            if isinstance(client, MockRedisClient):
                return False
            
            result = client.ping()
            logger.info("Redis connection test successful")
            return result
            
        except Exception as e:
            logger.error(f"Redis connection test failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> dict:
        if self.config.demo_mode:
            return {
                'host': 'local_storage',
                'port': 'N/A',
                'database': 'local_files',
                'ssl_enabled': False,
                'password_protected': False,
                'connected': True,
                'client_type': 'LocalStorageAdapter',
                'mode': 'demo'
            }
        else:
            return {
                'host': self.config.redis_host,
                'port': self.config.redis_port,
                'database': self.config.redis_db,
                'ssl_enabled': self.config.redis_ssl,
                'password_protected': bool(self.config.redis_password),
                'connected': self.test_connection(),
                'client_type': type(self._client).__name__ if self._client else 'None',
                'mode': 'production'
            }


class MockRedisClient:
    
    def __init__(self):
        self._data = {}
        logger.info("Mock Redis client initialized")
    
    def ping(self):
        return True
    
    def set(self, key, value):
        self._data[key] = value
        return True
    
    def get(self, key):
        return self._data.get(key)
    
    def delete(self, *keys):
        count = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                count += 1
        return count
    
    def exists(self, key):
        return key in self._data
    
    def keys(self, pattern="*"):
        if pattern == "*":
            return list(self._data.keys())
        # Simple pattern matching for basic patterns
        import fnmatch
        return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]


def create_redis_manager() -> RedisConnectionManager:
    config = RedisConfig()
    manager = RedisConnectionManager(config)
    
    # Log connection info
    info = manager.get_connection_info()
    logger.info(f"Redis manager created - Connected: {info['connected']}, Type: {info['client_type']}")
    
    return manager


# Global instance for easy access
redis_manager = create_redis_manager()


def get_redis_saver():
    return redis_manager.get_saver()


def get_redis_client():
    return redis_manager.get_client()


def test_storage_connection() -> bool:
    """Test storage connection (Redis or local storage)"""
    try:
        client = get_redis_client()
        result = client.ping()
        if result:
            logger.info("✅ Storage connection successful")
            return True
        else:
            logger.warning("⚠️ Storage ping returned False")
            return False
    except Exception as e:
        logger.error(f"❌ Storage connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test the storage system
    print("🧪 Testing Storage System...")
    
    # Test connection
    if test_storage_connection():
        print("✅ Storage system working!")
        
        # Test basic operations
        client = get_redis_client()
        client.set("demo_test", "agriculture_system_ready")
        value = client.get("demo_test")
        print(f"✅ Test value: {value}")
        
        # Test saver
        saver = get_redis_saver()
        print(f"✅ Checkpoint saver: {type(saver).__name__}")
        
    else:
        print("❌ Storage system failed")
        
    print("🌾 Agriculture system ready for demo!")
