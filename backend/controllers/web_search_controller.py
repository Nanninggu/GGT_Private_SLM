from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

from services.web_search_service import WebSearchService
from services.vector_service import VectorService
from services.langchain_vector_service import LangChainVectorService
from models.chat import ChatMessage
from utils.helpers import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web-search", tags=["web-search"])

class WebSearchRequest(BaseModel):
    query: str
    num_results: int = 10
    collection_name: Optional[str] = None

class WebSearchResponse(BaseModel):
    success: bool
    message: str
    results: List[dict]
    collection_name: Optional[str] = None

class WebSearchAndSaveRequest(BaseModel):
    query: str
    num_results: int = 10
    collection_name: str
    auto_save: bool = True

@router.post("/search", response_model=WebSearchResponse)
async def search_web(request: WebSearchRequest):
    """웹 검색을 수행합니다."""
    try:
        web_search_service = WebSearchService()
        
        # 웹 검색 실행
        search_results = await web_search_service.search_web(
            query=request.query,
            num_results=request.num_results
        )
        
        # 결과를 딕셔너리로 변환
        results = []
        for result in search_results:
            results.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "content": result.content,
                "domain": result.domain
            })
        
        return WebSearchResponse(
            success=True,
            message=f"웹 검색이 완료되었습니다. {len(results)}개의 결과를 찾았습니다.",
            results=results,
            collection_name=request.collection_name
        )
        
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"웹 검색 중 오류가 발생했습니다: {str(e)}")

@router.post("/search-and-save", response_model=WebSearchResponse)
async def search_and_save_to_collection(
    request: WebSearchAndSaveRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id)
):
    """웹 검색을 수행하고 결과를 컬렉션에 저장합니다."""
    try:
        web_search_service = WebSearchService()
        vector_service = VectorService()
        langchain_vector_service = LangChainVectorService()
        
        # 웹 검색 실행
        search_results = await web_search_service.search_web(
            query=request.query,
            num_results=request.num_results
        )
        
        if not search_results:
            return WebSearchResponse(
                success=False,
                message="검색 결과가 없습니다.",
                results=[],
                collection_name=request.collection_name
            )
        
        # 컬렉션 존재 확인 및 생성
        try:
            await vector_service.get_collection(request.collection_name)
        except:
            # 컬렉션이 없으면 생성
            await vector_service.create_collection(request.collection_name)
        
        # 검색 결과를 저장용 형식으로 변환
        formatted_results = web_search_service.format_search_results_for_storage(search_results)
        
        # 백그라운드에서 벡터 저장
        if request.auto_save:
            background_tasks.add_task(
                _save_search_results_to_collection,
                formatted_results,
                request.collection_name,
                current_user_id
            )
        
        # 결과를 딕셔너리로 변환
        results = []
        for result in search_results:
            results.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "content": result.content,
                "domain": result.domain
            })
        
        return WebSearchResponse(
            success=True,
            message=f"웹 검색이 완료되었습니다. {len(results)}개의 결과를 찾았고, 컬렉션 '{request.collection_name}'에 저장 중입니다.",
            results=results,
            collection_name=request.collection_name
        )
        
    except Exception as e:
        logger.error(f"Web search and save failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"웹 검색 및 저장 중 오류가 발생했습니다: {str(e)}")

async def _save_search_results_to_collection(
    formatted_results: List[dict],
    collection_name: str,
    user_id: str
):
    """백그라운드에서 검색 결과를 컬렉션에 저장합니다."""
    try:
        vector_service = VectorService()
        langchain_vector_service = LangChainVectorService()
        
        for result in formatted_results:
            # 벡터 저장
            await vector_service.add_document(
                collection_name=collection_name,
                content=result["content"],
                metadata={
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"],
                    "domain": result["domain"],
                    "source": "web_search",
                    "user_id": user_id,
                    **result["metadata"]
                }
            )
        
        logger.info(f"Successfully saved {len(formatted_results)} web search results to collection '{collection_name}'")
        
    except Exception as e:
        logger.error(f"Failed to save search results to collection: {str(e)}")

@router.get("/collections")
async def get_available_collections(current_user_id: str = Depends(get_current_user_id)):
    """사용 가능한 컬렉션 목록을 반환합니다."""
    try:
        vector_service = VectorService()
        collections = await vector_service.list_collections()
        
        return {
            "success": True,
            "collections": collections
        }
        
    except Exception as e:
        logger.error(f"Failed to get collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"컬렉션 목록을 가져오는 중 오류가 발생했습니다: {str(e)}")
