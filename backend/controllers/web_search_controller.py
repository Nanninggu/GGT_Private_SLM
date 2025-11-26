from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

from backend.services.web_search_service import WebSearchService
from backend.services.vector_service import VectorService
from backend.services.langchain_vector_service import LangChainVectorService
from backend.models.chat import ChatMessage
from backend.models.user import User
from backend.controllers.auth_controller import auth_controller
# from utils.helpers import get_current_user_id  # Not needed for web search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/web-search", tags=["web-search"])

class WebSearchRequest(BaseModel):
    query: str
    num_results: int = 10
    collection_name: Optional[str] = None
    search_engine: Optional[str] = "duckduckgo"

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
    search_engine: Optional[str] = "duckduckgo"

@router.post("/search", response_model=WebSearchResponse)
async def search_web(request: WebSearchRequest):
    """웹 검색을 수행합니다."""
    try:
        web_search_service = WebSearchService()
        
        # 검색 엔진 설정
        if request.search_engine:
            web_search_service.search_engine = request.search_engine
            logger.info(f"Using search engine: {web_search_service.search_engine}")
        
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
    current_user: User = Depends(auth_controller.get_current_user)
):
    """웹 검색을 수행하고 결과를 컬렉션에 저장합니다."""
    try:
        web_search_service = WebSearchService()
        vector_service = VectorService()
        langchain_vector_service = LangChainVectorService()
        
        # 검색 엔진 설정
        if request.search_engine:
            web_search_service.search_engine = request.search_engine
            logger.info(f"Using search engine: {web_search_service.search_engine}")
        
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
        
        # 컬렉션 존재 확인 및 생성 (LangChain RAG 서비스 사용)
        try:
            collection_info = await langchain_vector_service.get_collection_info(request.collection_name)
            # 기존 컬렉션의 소유권 확인
            collection_user_id = collection_info.get("user_id") if collection_info else None
            if collection_user_id is not None and collection_user_id != current_user.id:
                raise HTTPException(
                    status_code=403, 
                    detail=f"You don't have permission to save to collection '{request.collection_name}'. Only the collection owner can save files."
                )
            elif collection_user_id is None:
                # Shared collections (user_id = NULL) - check created_by in metadata
                metadata = collection_info.get("metadata", {}) if collection_info else {}
                created_by = metadata.get("created_by")
                if created_by != current_user.id:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"You don't have permission to save to collection '{request.collection_name}'. Only the collection owner can save files."
                    )
        except HTTPException:
            raise
        except:
            # 컬렉션이 없으면 생성 (사용자 ID 포함)
            try:
                await langchain_vector_service.create_collection(
                    request.collection_name, 
                    f"웹 검색 결과를 위한 컬렉션: {request.collection_name}",
                    current_user.id,
                    is_shared=False  # Mark as personal collection
                )
            except ValueError as e:
                if "already exists" in str(e):
                    # 컬렉션이 이미 존재하는 경우, 계속 진행
                    logger.info(f"Collection '{request.collection_name}' already exists, continuing...")
                else:
                    raise
        
        # 검색 결과를 저장용 형식으로 변환
        formatted_results = web_search_service.format_search_results_for_storage(search_results)
        
        # 벡터 저장 (동기적으로 실행)
        save_success = False
        save_error = None
        if request.auto_save:
            try:
                await _save_search_results_to_collection(
                    formatted_results,
                    request.collection_name
                )
                save_success = True
                logger.info(f"Successfully saved web search results to collection '{request.collection_name}'")
            except Exception as e:
                save_error = str(e)
                logger.error(f"Failed to save search results: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # 저장 실패해도 검색 결과는 반환
        
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
        
        if save_success:
            message = f"웹 검색이 완료되었습니다. {len(results)}개의 결과를 찾았고, 컬렉션 '{request.collection_name}'에 저장되었습니다."
        else:
            message = f"웹 검색이 완료되었습니다. {len(results)}개의 결과를 찾았습니다. (저장 실패: {save_error})"
        
        return WebSearchResponse(
            success=True,
            message=message,
            results=results,
            collection_name=request.collection_name
        )
        
    except Exception as e:
        logger.error(f"Web search and save failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"웹 검색 및 저장 중 오류가 발생했습니다: {str(e)}")

async def _save_search_results_to_collection(
    formatted_results: List[dict],
    collection_name: str
):
    """백그라운드에서 검색 결과를 컬렉션에 저장합니다."""
    try:
        logger.info(f"Starting to save {len(formatted_results)} web search results to collection '{collection_name}'")
        
        langchain_vector_service = LangChainVectorService()
        
        # 벡터 서비스 초기화
        logger.info("Initializing LangChain vector service...")
        await langchain_vector_service.initialize()
        logger.info("LangChain vector service initialized successfully")
        
        # 컬렉션 설정
        logger.info(f"Setting collection to '{collection_name}'...")
        await langchain_vector_service.set_collection(collection_name)
        logger.info(f"Collection '{collection_name}' set successfully")
        
        saved_count = 0
        for i, result in enumerate(formatted_results):
            try:
                logger.info(f"Saving document {i+1}/{len(formatted_results)}: {result.get('title', 'Unknown')}")
                
                # LangChain RAG 서비스를 사용하여 벡터 저장
                # collection_name을 명시적으로 전달하여 올바른 컬렉션에 저장되도록 보장
                doc_ids = await langchain_vector_service.add_document(
                    content=result["content"],
                    metadata={
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"],
                        "domain": result["domain"],
                        "source": "web_search",
                        "user_id": "web_search_user",
                        **result["metadata"]
                    },
                    collection_name=collection_name  # 컬렉션 이름 명시적으로 전달
                )
                
                logger.info(f"Document {i+1} saved successfully with {len(doc_ids)} chunks")
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Failed to save document {i+1}: {str(e)}")
                continue
        
        logger.info(f"Successfully saved {saved_count}/{len(formatted_results)} web search results to collection '{collection_name}'")
        
    except Exception as e:
        logger.error(f"Failed to save search results to collection: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

@router.get("/collections")
async def get_available_collections():
    """사용 가능한 컬렉션 목록을 반환합니다."""
    try:
        langchain_vector_service = LangChainVectorService()
        collections = await langchain_vector_service.get_collections()
        
        return {
            "success": True,
            "collections": collections
        }
        
    except Exception as e:
        logger.error(f"Failed to get collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"컬렉션 목록을 가져오는 중 오류가 발생했습니다: {str(e)}")
