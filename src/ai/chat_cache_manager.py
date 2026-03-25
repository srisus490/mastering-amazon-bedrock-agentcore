"""Cache manager for chat responses to optimize costs."""

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class ChatCacheManager:
    """Manages caching of chat responses to reduce Bedrock API calls."""
    
    # Cache configuration
    MAX_CACHE_SIZE = 1000  # Maximum number of cached entries
    DEFAULT_TTL_SECONDS = 300  # 5 minutes for data queries
    STATIC_TTL_SECONDS = 3600  # 1 hour for static queries
    
    def __init__(self):
        """Initialize the cache manager."""
        # Use OrderedDict for LRU eviction
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._hit_count = 0
        self._miss_count = 0
    
    def getCachedResponse(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response if available and not expired.
        
        Args:
            query_hash: Hash key for the query
            
        Returns:
            Cached response dict or None if not found/expired
        """
        if query_hash not in self._cache:
            self._miss_count += 1
            logger.debug(f"Cache miss for query hash: {query_hash[:16]}...")
            return None
        
        entry = self._cache[query_hash]
        
        # Check if expired
        if time.time() > entry['expires_at']:
            # Remove expired entry
            del self._cache[query_hash]
            self._miss_count += 1
            logger.debug(f"Cache expired for query hash: {query_hash[:16]}...")
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(query_hash)
        self._hit_count += 1
        
        logger.debug(
            f"Cache hit for query hash: {query_hash[:16]}...",
            hit_rate=self.getHitRate()
        )
        
        return entry['response']
    
    def setCachedResponse(
        self,
        query_hash: str,
        response: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """
        Store a response in the cache.
        
        Args:
            query_hash: Hash key for the query
            response: Response data to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.DEFAULT_TTL_SECONDS
        
        # Check cache size and evict oldest if necessary
        if len(self._cache) >= self.MAX_CACHE_SIZE:
            # Remove oldest entry (first item in OrderedDict)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key[:16]}...")
        
        # Store new entry
        self._cache[query_hash] = {
            'response': response,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        
        logger.debug(
            f"Cached response for query hash: {query_hash[:16]}...",
            ttl=ttl,
            cache_size=len(self._cache)
        )
    
    def generateQueryHash(
        self,
        query: str,
        context: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a hash key for a query and its context.
        
        Args:
            query: User's query string
            context: Conversation context messages
            
        Returns:
            SHA256 hash string
        """
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        
        # Include relevant context (last 2 messages for context-dependent queries)
        context_str = ""
        if context:
            recent_context = context[-2:]
            context_str = json.dumps(
                [{'role': m.role, 'content': m.content} for m in recent_context],
                sort_keys=True
            )
        
        # Combine query and context
        cache_key_data = f"{normalized_query}|{context_str}"
        
        # Generate hash
        hash_obj = hashlib.sha256(cache_key_data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def clearCache(self, query_hash: Optional[str] = None) -> None:
        """
        Clear cached responses.
        
        Args:
            query_hash: Specific hash to clear, or None to clear all
        """
        if query_hash:
            if query_hash in self._cache:
                del self._cache[query_hash]
                logger.info(f"Cleared cache entry: {query_hash[:16]}...")
        else:
            self._cache.clear()
            logger.info("Cleared all cache entries")
    
    def getHitRate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Hit rate as a percentage (0-100)
        """
        total_requests = self._hit_count + self._miss_count
        if total_requests == 0:
            return 0.0
        
        return (self._hit_count / total_requests) * 100
    
    def getCacheStats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'size': len(self._cache),
            'max_size': self.MAX_CACHE_SIZE,
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': self.getHitRate(),
            'total_requests': self._hit_count + self._miss_count
        }
    
    def cleanExpiredEntries(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)


# Global cache instance
_global_cache = None


def get_chat_cache() -> ChatCacheManager:
    """
    Get the global chat cache instance.
    
    Returns:
        ChatCacheManager instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ChatCacheManager()
    return _global_cache
