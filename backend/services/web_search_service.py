import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from backend.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    content: Optional[str] = None
    domain: Optional[str] = None

class WebSearchService:
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.google_cse_id = settings.GOOGLE_CSE_ID
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        
        if not self.google_api_key or not self.google_cse_id:
            logger.warning("Google API credentials not found. Web search will be limited.")
        
        if not self.serpapi_key:
            logger.warning("SerpAPI key not found. Using Google Custom Search only.")
    
    async def search_web(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """웹 검색을 수행하고 결과를 반환합니다."""
        try:
            # Google Custom Search API 사용
            if self.google_api_key and self.google_cse_id:
                results = await self._search_with_google(query, num_results)
            else:
                # SerpAPI 사용 (대안)
                results = await self._search_with_serpapi(query, num_results)
            
            # 검색 결과의 내용을 추출
            enriched_results = await self._enrich_search_results(results)
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return []
    
    async def _search_with_google(self, query: str, num_results: int) -> List[SearchResult]:
        """Google Custom Search API를 사용하여 검색합니다."""
        try:
            import asyncio
            import concurrent.futures
            
            def _sync_google_search():
                service = build("customsearch", "v1", developerKey=self.google_api_key)
                
                # 검색 실행
                result = service.cse().list(
                    q=query,
                    cx=self.google_cse_id,
                    num=min(num_results, 10)  # Google API는 최대 10개까지
                ).execute()
                
                search_results = []
                for item in result.get("items", []):
                    search_results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        domain=self._extract_domain(item.get("link", ""))
                    ))
                
                return search_results
            
            # 비동기적으로 실행
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                search_results = await loop.run_in_executor(executor, _sync_google_search)
            
            return search_results
            
        except HttpError as e:
            logger.error(f"Google API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Google search error: {str(e)}")
            return []
    
    async def _search_with_serpapi(self, query: str, num_results: int) -> List[SearchResult]:
        """SerpAPI를 사용하여 검색합니다."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": num_results,
                    "engine": "google"
                }
                
                async with session.get("https://serpapi.com/search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        search_results = []
                        
                        for result in data.get("organic_results", []):
                            search_results.append(SearchResult(
                                title=result.get("title", ""),
                                url=result.get("link", ""),
                                snippet=result.get("snippet", ""),
                                domain=self._extract_domain(result.get("link", ""))
                            ))
                        
                        return search_results
                    else:
                        logger.error(f"SerpAPI error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"SerpAPI search failed: {str(e)}")
            return []
    
    async def _enrich_search_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """검색 결과의 내용을 추출하여 풍부하게 만듭니다."""
        enriched_results = []
        
        for result in results:
            try:
                # 웹페이지 내용 추출
                content = await self._extract_webpage_content(result.url)
                result.content = content
                enriched_results.append(result)
                
                # API 제한을 고려하여 딜레이
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Failed to extract content from {result.url}: {str(e)}")
                enriched_results.append(result)
        
        return enriched_results
    
    async def _extract_webpage_content(self, url: str) -> str:
        """웹페이지의 텍스트 내용을 추출합니다."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 불필요한 태그 제거
                        for script in soup(["script", "style", "nav", "footer", "header"]):
                            script.decompose()
                        
                        # 텍스트 추출
                        text = soup.get_text()
                        
                        # 텍스트 정제
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        # 길이 제한 (너무 긴 내용은 잘라냄)
                        if len(text) > 5000:
                            text = text[:5000] + "..."
                        
                        return text
                    else:
                        return ""
                        
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {str(e)}")
            return ""
    
    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인을 추출합니다."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    def format_search_results_for_storage(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """검색 결과를 저장용 형식으로 변환합니다."""
        formatted_results = []
        
        for result in results:
            formatted_results.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "content": result.content or result.snippet,
                "domain": result.domain,
                "source": "web_search",
                "metadata": {
                    "search_type": "web",
                    "url": result.url,
                    "domain": result.domain
                }
            })
        
        return formatted_results
