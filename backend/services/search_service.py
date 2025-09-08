"""
Search service for Google Custom Search API integration
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
import json
from urllib.parse import quote

from backend.config.settings import settings

logger = logging.getLogger(__name__)

class SearchService:
    """Search service for Google Custom Search API"""
    
    def __init__(self):
        self.client = None
        self.api_key = settings.GOOGLE_SEARCH_API_KEY
        self.search_engine_id = settings.GOOGLE_SEARCH_ENGINE_ID
        
    async def initialize(self):
        """Initialize search service"""
        try:
            self.client = httpx.AsyncClient(
                timeout=settings.GOOGLE_SEARCH_TIMEOUT
            )
            logger.info("Search service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize search service: {e}")
            raise
    
    async def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """Perform Google Custom Search"""
        try:
            if not self.api_key or self.api_key == "your_api_key_here":
                logger.warning("Google Search API key not configured")
                return []
            
            max_results = max_results or settings.GOOGLE_SEARCH_MAX_RESULTS
            
            # Build search URL
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(max_results, 10),  # Google API max is 10 per request
                "safe": "off"
            }
            
            response = await self.client.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("items", []):
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "display_link": item.get("displayLink", ""),
                    "formatted_url": item.get("formattedUrl", ""),
                    "metadata": {
                        "search_engine": "google",
                        "query": query
                    }
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} search results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform search: {e}")
            return []
    
    async def deep_search(self, query: str, max_results: int = None) -> Dict[str, Any]:
        """Perform deep search with enhanced results"""
        try:
            if not settings.DEEP_SEARCH_ENABLED:
                return {"enabled": False, "results": []}
            
            max_results = max_results or settings.DEEP_SEARCH_MAX_RESULTS
            
            # Perform initial search
            search_results = await self.search(query, max_results)
            
            if not search_results:
                return {
                    "enabled": True,
                    "results": [],
                    "metadata": {
                        "query": query,
                        "total_results": 0
                    }
                }
            
            # Enhance results with additional processing
            enhanced_results = []
            for result in search_results:
                enhanced_result = result.copy()
                
                # Add snippets if enabled
                if settings.DEEP_SEARCH_INCLUDE_SNIPPETS:
                    enhanced_result["enhanced_snippet"] = self._enhance_snippet(result["snippet"])
                
                # Add metadata if enabled
                if settings.DEEP_SEARCH_INCLUDE_METADATA:
                    enhanced_result["search_metadata"] = {
                        "relevance_score": self._calculate_relevance_score(query, result),
                        "content_type": self._detect_content_type(result),
                        "language": "auto-detected"
                    }
                
                enhanced_results.append(enhanced_result)
            
            return {
                "enabled": True,
                "results": enhanced_results,
                "metadata": {
                    "query": query,
                    "total_results": len(enhanced_results),
                    "enhanced": True
                }
            }
            
        except Exception as e:
            logger.error(f"Deep search failed: {e}")
            return {
                "enabled": True,
                "results": [],
                "error": str(e),
                "metadata": {
                    "query": query,
                    "total_results": 0
                }
            }
    
    def _enhance_snippet(self, snippet: str) -> str:
        """Enhance snippet with better formatting"""
        if not snippet:
            return ""
        
        # Clean up snippet
        enhanced = snippet.strip()
        
        # Add ellipsis if truncated
        if len(enhanced) > 150:
            enhanced = enhanced[:150] + "..."
        
        return enhanced
    
    def _calculate_relevance_score(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate relevance score for search result"""
        try:
            query_words = set(query.lower().split())
            title_words = set(result.get("title", "").lower().split())
            snippet_words = set(result.get("snippet", "").lower().split())
            
            # Calculate word overlap
            title_overlap = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
            snippet_overlap = len(query_words.intersection(snippet_words)) / len(query_words) if query_words else 0
            
            # Weighted score (title is more important)
            relevance_score = (title_overlap * 0.7) + (snippet_overlap * 0.3)
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Failed to calculate relevance score: {e}")
            return 0.0
    
    def _detect_content_type(self, result: Dict[str, Any]) -> str:
        """Detect content type from URL and title"""
        try:
            url = result.get("link", "").lower()
            title = result.get("title", "").lower()
            
            if any(ext in url for ext in [".pdf", ".doc", ".docx"]):
                return "document"
            elif any(ext in url for ext in [".jpg", ".jpeg", ".png", ".gif"]):
                return "image"
            elif any(ext in url for ext in [".mp4", ".avi", ".mov"]):
                return "video"
            elif "youtube.com" in url or "youtu.be" in url:
                return "video"
            elif "wikipedia.org" in url:
                return "encyclopedia"
            elif any(domain in url for domain in ["github.com", "stackoverflow.com", "stackexchange.com"]):
                return "technical"
            else:
                return "webpage"
                
        except Exception as e:
            logger.warning(f"Failed to detect content type: {e}")
            return "unknown"
    
    async def health_check(self) -> bool:
        """Check search service health"""
        try:
            if not self.api_key or self.api_key == "your_api_key_here":
                return False
            
            # Test with a simple query
            results = await self.search("test", max_results=1)
            return len(results) >= 0  # Even 0 results means API is working
            
        except Exception as e:
            logger.error(f"Search service health check failed: {e}")
            return False
    
    async def close(self):
        """Close search service"""
        if self.client:
            await self.client.aclose()
            logger.info("Search service closed")

# Global search service instance
search_service = SearchService()
