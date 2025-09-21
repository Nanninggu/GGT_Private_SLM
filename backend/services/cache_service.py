"""
Cache service for vector database optimization
"""
import asyncio
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Cache service for vector search results and embeddings"""
    
    def __init__(self):
        self.embedding_cache: Dict[str, List[float]] = {}
        self.search_cache: Dict[str, Dict[str, Any]] = {}
        self.chat_response_cache: Dict[str, str] = {}  # 전용 채팅 응답 캐시
        self.cache_stats = {
            "embedding_hits": 0,
            "embedding_misses": 0,
            "search_hits": 0,
            "search_misses": 0,
            "chat_hits": 0,
            "chat_misses": 0,
            "cache_size": 0
        }
        self.max_cache_size = settings.VECTOR_DB_CACHE_SIZE
        self.cache_ttl = 3600  # 1 hour TTL
        self.chat_cache_ttl = 1800  # 30 minutes for chat responses
        
    def _generate_cache_key(self, text: str, prefix: str = "") -> str:
        """Generate cache key for text"""
        content = f"{prefix}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float, ttl: float = None) -> bool:
        """Check if cache entry is expired"""
        ttl = ttl or self.cache_ttl
        return time.time() - timestamp > ttl
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        
        # Clean embedding cache
        expired_keys = [
            key for key, (_, timestamp) in self.embedding_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.embedding_cache[key]
        
        # Clean search cache
        expired_keys = [
            key for key, (_, timestamp) in self.search_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        for key in expired_keys:
            del self.search_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _evict_oldest(self, cache_dict: Dict[str, Any]):
        """Evict oldest entries when cache is full"""
        if len(cache_dict) >= self.max_cache_size:
            # Remove oldest 10% of entries
            items_to_remove = len(cache_dict) // 10
            sorted_items = sorted(cache_dict.items(), key=lambda x: x[1][1])  # Sort by timestamp
            for key, _ in sorted_items[:items_to_remove]:
                del cache_dict[key]
            logger.info(f"Evicted {items_to_remove} oldest cache entries")
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        cache_key = self._generate_cache_key(text, "embedding")
        
        if cache_key in self.embedding_cache:
            embedding, timestamp = self.embedding_cache[cache_key]
            if not self._is_expired(timestamp):
                self.cache_stats["embedding_hits"] += 1
                return embedding
            else:
                del self.embedding_cache[cache_key]
        
        self.cache_stats["embedding_misses"] += 1
        return None
    
    async def set_embedding(self, text: str, embedding: List[float]):
        """Store embedding in cache"""
        cache_key = self._generate_cache_key(text, "embedding")
        timestamp = time.time()
        
        # Cleanup if needed
        self._cleanup_expired()
        self._evict_oldest(self.embedding_cache)
        
        self.embedding_cache[cache_key] = (embedding, timestamp)
        self.cache_stats["cache_size"] = len(self.embedding_cache) + len(self.search_cache)
    
    async def get_search_results(self, query: str, top_k: int, similarity_threshold: float) -> Optional[List[Dict[str, Any]]]:
        """Get search results from cache"""
        cache_key = self._generate_cache_key(f"{query}:{top_k}:{similarity_threshold}", "search")
        
        if cache_key in self.search_cache:
            results, timestamp = self.search_cache[cache_key]
            if not self._is_expired(timestamp):
                self.cache_stats["search_hits"] += 1
                return results
            else:
                del self.search_cache[cache_key]
        
        self.cache_stats["search_misses"] += 1
        return None
    
    async def set_search_results(self, query: str, top_k: int, similarity_threshold: float, results: List[Dict[str, Any]]):
        """Store search results in cache"""
        cache_key = self._generate_cache_key(f"{query}:{top_k}:{similarity_threshold}", "search")
        timestamp = time.time()
        
        # Cleanup if needed
        self._cleanup_expired()
        self._evict_oldest(self.search_cache)
        
        self.search_cache[cache_key] = (results, timestamp)
        self.cache_stats["cache_size"] = len(self.embedding_cache) + len(self.search_cache)
    
    async def get_chat_response(self, query: str, rag_mode: str) -> Optional[str]:
        """Get cached chat response with dedicated cache"""
        cache_key = self._generate_cache_key(f"{query}:{rag_mode}", "chat")
        
        if cache_key in self.chat_response_cache:
            response, timestamp = self.chat_response_cache[cache_key]
            if not self._is_expired(timestamp, self.chat_cache_ttl):
                self.cache_stats["chat_hits"] += 1
                logger.debug(f"Chat cache hit for query: {query[:50]}...")
                return response
            else:
                del self.chat_response_cache[cache_key]
        
        self.cache_stats["chat_misses"] += 1
        return None
    
    async def set_chat_response(self, query: str, rag_mode: str, response: str):
        """Store chat response in dedicated cache"""
        cache_key = self._generate_cache_key(f"{query}:{rag_mode}", "chat")
        timestamp = time.time()
        
        # Cleanup if needed
        self._cleanup_expired()
        self._evict_oldest(self.chat_response_cache)
        
        self.chat_response_cache[cache_key] = (response, timestamp)
        self.cache_stats["cache_size"] = len(self.embedding_cache) + len(self.search_cache) + len(self.chat_response_cache)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = (self.cache_stats["embedding_hits"] + self.cache_stats["embedding_misses"] + 
                         self.cache_stats["search_hits"] + self.cache_stats["search_misses"] +
                         self.cache_stats["chat_hits"] + self.cache_stats["chat_misses"])
        
        embedding_hit_rate = (self.cache_stats["embedding_hits"] / 
                            max(1, self.cache_stats["embedding_hits"] + self.cache_stats["embedding_misses"])) * 100
        
        search_hit_rate = (self.cache_stats["search_hits"] / 
                         max(1, self.cache_stats["search_hits"] + self.cache_stats["search_misses"])) * 100
        
        chat_hit_rate = (self.cache_stats["chat_hits"] / 
                        max(1, self.cache_stats["chat_hits"] + self.cache_stats["chat_misses"])) * 100
        
        return {
            "embedding_cache_size": len(self.embedding_cache),
            "search_cache_size": len(self.search_cache),
            "chat_cache_size": len(self.chat_response_cache),
            "total_cache_size": self.cache_stats["cache_size"],
            "embedding_hit_rate": round(embedding_hit_rate, 2),
            "search_hit_rate": round(search_hit_rate, 2),
            "chat_hit_rate": round(chat_hit_rate, 2),
            "total_requests": total_requests,
            "cache_ttl": self.cache_ttl,
            "chat_cache_ttl": self.chat_cache_ttl
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.embedding_cache.clear()
        self.search_cache.clear()
        self.chat_response_cache.clear()
        self.cache_stats = {
            "embedding_hits": 0,
            "embedding_misses": 0,
            "search_hits": 0,
            "search_misses": 0,
            "chat_hits": 0,
            "chat_misses": 0,
            "cache_size": 0
        }
        logger.info("All caches cleared")
    
    async def preload_embeddings(self, texts: List[str], embedding_func):
        """Preload embeddings for common texts"""
        logger.info(f"Preloading {len(texts)} embeddings")
        
        for text in texts:
            if await self.get_embedding(text) is None:
                try:
                    embedding = await embedding_func(text)
                    await self.set_embedding(text, embedding)
                except Exception as e:
                    logger.warning(f"Failed to preload embedding for text: {e}")
        
        logger.info("Embedding preloading completed")

# Global cache service instance
cache_service = CacheService()
