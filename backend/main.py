"""
FastAPI backend server for the chatbot
Converted from Spring Boot with enhanced RAG capabilities
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
import logging
import asyncio
import uuid
import json
from datetime import datetime
from contextlib import asynccontextmanager

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ChatController is now replaced by direct chat_service usage
from backend.controllers.auth_controller import auth_controller
from backend.controllers.web_search_controller import router as web_search_router
from backend.controllers.accuracy_controller import AccuracyController
from backend.controllers.performance_controller import PerformanceController
from backend.services.auth_service import auth_service
from backend.models.user import User
from backend.config.settings import settings
from backend.services.database_service import db_service
from backend.services.vector_service import vector_service
from backend.services.ollama_service import ollama_service
from backend.services.rag_service import rag_service
from backend.services.search_service import search_service
from backend.services.langchain_rag_service import langchain_rag_service
from backend.services.prompt_service import prompt_service
from backend.services.file_processing_service import FileProcessingService
from backend.services.markdown_service import MarkdownService
from backend.services.accuracy_service import accuracy_service
from backend.services.chat_service import ChatService
from backend.services.cache_service import cache_service
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL_APP),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    rag_mode: Optional[str] = "LangChain RAG"
    model_type: Optional[str] = "fast"
    collection_names: Optional[List[str]] = None

class CollectionRequest(BaseModel):
    collection_name: str

class CreateCollectionRequest(BaseModel):
    collection_name: str
    description: Optional[str] = ""
    type: Optional[str] = "personal"  # "personal" or "shared"

class RenameCollectionRequest(BaseModel):
    old_name: str
    new_name: str

class CollectionResponse(BaseModel):
    success: bool
    collections: Optional[List[Dict[str, Any]]] = None
    current_collection: Optional[str] = None
    error: Optional[str] = None

# Global services
services_initialized = False
chat_service = ChatService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global services_initialized
    
    # Startup
    logger.info("Starting up services...")
    try:
        await db_service.initialize()
        await vector_service.initialize()
        await ollama_service.initialize()
        await rag_service.initialize()
        await search_service.initialize()
        # Temporarily disable LangChain RAG service due to pgvector issues
        # await langchain_rag_service.initialize()
        await accuracy_service.initialize()
        await chat_service.initialize()
        services_initialized = True
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    try:
        await db_service.close()
        await vector_service.close()
        await ollama_service.close()
        await rag_service.close()
        await search_service.close()
        logger.info("All services closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize controller and services
accuracy_controller = AccuracyController()
performance_controller = PerformanceController()
markdown_service = MarkdownService()

# Include routers
app.include_router(web_search_router)

# Request models
class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_rag: bool = True  # RAG is enabled by default
    use_search: bool = False
    rag_mode: Optional[str] = "LangChain RAG"  # RAG mode selection
    model_type: Optional[str] = "fast"  # Model type selection
    custom_params: Optional[Dict[str, Any]] = None  # 사용자 맞춤 설정
    collection_names: Optional[List[str]] = None  # 선택된 데이터셋 목록

class SessionRequest(BaseModel):
    session_id: str

class DocumentRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = None
    deep_search: bool = False

class MarkdownExportRequest(BaseModel):
    session_id: str
    session_name: Optional[str] = "채팅 기록"
    include_metadata: bool = True

class UpdateSessionTitleRequest(BaseModel):
    title: str
    user_id: Optional[str] = "default"

class UpdateSessionDescriptionRequest(BaseModel):
    description: str
    user_id: Optional[str] = "default"

class SingleMessageMarkdownRequest(BaseModel):
    message: Dict[str, Any]
    include_metadata: bool = True

# Authentication models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# Accuracy measurement models
class AccuracyQueryRequest(BaseModel):
    query: str
    expected_answer: Optional[str] = None

class AccuracyTestSuiteRequest(BaseModel):
    test_queries: List[Dict[str, str]]

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check services
        ollama_healthy = await ollama_service.health_check()
        search_healthy = await search_service.health_check()
        
        return {
            "status": "healthy" if services_initialized else "unhealthy",
            "services": {
                "database": "healthy",
                "vector_db": "healthy",
                "ollama": "healthy" if ollama_healthy else "unhealthy",
                "search": "healthy" if search_healthy else "unhealthy"
            },
            "app_name": settings.APP_NAME,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# Performance monitoring endpoints
@app.get("/api/performance/vector-stats")
async def get_vector_performance_stats():
    """Get vector database performance statistics"""
    return await performance_controller.get_vector_performance_stats()

@app.get("/api/performance/cache-stats")
async def get_cache_stats():
    """Get cache performance statistics"""
    return await performance_controller.get_cache_stats()

@app.post("/api/performance/clear-cache")
async def clear_cache():
    """Clear all caches"""
    return await performance_controller.clear_cache()

@app.post("/api/performance/preload-embeddings")
async def preload_embeddings(request: dict):
    """Preload common embeddings for better performance"""
    texts = request.get("texts", [])
    return await performance_controller.preload_embeddings(texts)

@app.get("/api/performance/database-stats")
async def get_database_stats():
    """Get database performance statistics"""
    return await performance_controller.get_database_stats()

@app.post("/api/performance/optimize-database")
async def optimize_database():
    """Run database optimization tasks"""
    return await performance_controller.optimize_database()

@app.get("/api/performance/real-time")
async def get_real_time_performance():
    """Get real-time performance metrics"""
    try:
        # Get all performance metrics
        cache_stats = cache_service.get_cache_stats()
        vector_stats = await performance_controller.get_vector_performance_stats()
        db_stats = await performance_controller.get_database_stats()
        
        # Calculate overall performance score
        cache_score = cache_stats.get("chat_hit_rate", 0)
        vector_score = 100 if vector_stats.get("success") else 0
        db_score = 100 if db_stats.get("success") else 0
        
        overall_score = (cache_score + vector_score + db_score) / 3
        
        return {
            "success": True,
            "data": {
                "overall_score": round(overall_score, 2),
                "cache_performance": {
                    "hit_rate": cache_stats.get("chat_hit_rate", 0),
                    "total_requests": cache_stats.get("total_requests", 0),
                    "cache_size": cache_stats.get("total_cache_size", 0)
                },
                "vector_performance": vector_stats.get("data", {}),
                "database_performance": db_stats.get("data", {}),
                "timestamp": datetime.now().isoformat(),
                "status": "healthy" if overall_score > 70 else "needs_attention"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/performance/benchmark-chat")
async def benchmark_chat(request: dict):
    """Benchmark chat response performance with detailed metrics"""
    import time
    
    query = request.get("query", "안녕하세요")
    rag_mode = request.get("rag_mode", "LangChain RAG")
    iterations = request.get("iterations", 3)
    
    try:
        # Clear cache for fair comparison
        cache_service.clear_cache()
        
        # Test chat response times with detailed metrics
        response_times = []
        cache_hit_rates = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Simulate chat request
            if rag_mode == "기본 RAG":
                result = await rag_service.rag_query(query, "benchmark_session")
            else:
                result = await langchain_rag_service.rag_query(query, "benchmark_session")
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            # Check cache hit rate
            cache_stats = cache_service.get_cache_stats()
            cache_hit_rates.append(cache_stats.get("chat_hit_rate", 0))
        
        # Calculate statistics
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        avg_cache_hit_rate = sum(cache_hit_rates) / len(cache_hit_rates)
        
        # Enhanced performance grade with more granular levels
        if avg_time < 1.0:
            performance_grade = "A+ (Excellent - <1s)"
        elif avg_time < 2.0:
            performance_grade = "A (Very Good - <2s)"
        elif avg_time < 3.0:
            performance_grade = "B+ (Good - <3s)"
        elif avg_time < 5.0:
            performance_grade = "B (Acceptable - <5s)"
        elif avg_time < 10.0:
            performance_grade = "C (Fair - <10s)"
        elif avg_time < 20.0:
            performance_grade = "D (Poor - <20s)"
        else:
            performance_grade = "F (Needs Improvement - >20s)"
        
        return {
            "success": True,
            "data": {
                "query": query,
                "rag_mode": rag_mode,
                "iterations": iterations,
                "avg_response_time": round(avg_time, 4),
                "min_response_time": round(min_time, 4),
                "max_response_time": round(max_time, 4),
                "avg_cache_hit_rate": round(avg_cache_hit_rate, 2),
                "performance_grade": performance_grade,
                "response_times": [round(t, 4) for t in response_times],
                "cache_hit_rates": [round(r, 2) for r in cache_hit_rates]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/performance/benchmark-search")
async def benchmark_search(request: dict):
    """Benchmark search performance with and without optimization"""
    import time
    
    query = request.get("query", "test query")
    iterations = request.get("iterations", 5)
    
    try:
        # Clear cache for fair comparison
        cache_service.clear_cache()
        
        # Test optimized search
        optimized_times = []
        for i in range(iterations):
            start_time = time.time()
            await vector_service.search_similar_optimized(query)
            optimized_times.append(time.time() - start_time)
        
        # Test regular search
        regular_times = []
        for i in range(iterations):
            start_time = time.time()
            await vector_service.search_similar(query)
            regular_times.append(time.time() - start_time)
        
        # Calculate statistics
        avg_optimized = sum(optimized_times) / len(optimized_times)
        avg_regular = sum(regular_times) / len(regular_times)
        improvement = ((avg_regular - avg_optimized) / avg_regular) * 100
        
        return {
            "success": True,
            "data": {
                "query": query,
                "iterations": iterations,
                "optimized_avg_time": round(avg_optimized, 4),
                "regular_avg_time": round(avg_regular, 4),
                "improvement_percentage": round(improvement, 2),
                "optimized_times": [round(t, 4) for t in optimized_times],
                "regular_times": [round(t, 4) for t in regular_times]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/info")
async def info():
    """Application info endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "RAG-enabled chatbot with vector database and search capabilities",
        "features": [
            "Vector database (pgvector)",
            "Ollama LLM integration",
            "RAG (Retrieval-Augmented Generation)",
            "Google Custom Search API",
            "Deep search capabilities"
        ]
    }

@app.get("/api/test/login")
async def test_login():
    """Test login endpoint"""
    try:
        from backend.models.user import LoginRequest
        request = LoginRequest(username="test1234", password="test1234")
        result = await auth_controller.login(request)
        return {
            "success": result.success,
            "message": result.message,
            "user": result.user.username if result.user else None
        }
    except Exception as e:
        logger.error(f"Test login failed: {e}")
        return {"error": str(e)}

# Chat endpoints
@app.post("/api/chat/session")
async def create_session(current_user: User = Depends(auth_controller.get_current_user)):
    """Create a new chat session"""
    try:
        session = await chat_service.create_session(user_id=current_user.id)
        return {
            "success": True,
            "session_id": session.id,
            "created_at": session.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/save-message")
async def save_message(request: dict):
    """Save a message to a session with full metadata (sources, accuracy, etc.)"""
    try:
        message = request.get("message")
        session_id = request.get("session_id", "default")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Create a simple message object for saving
        from backend.models.chat import ChatMessage, MessageRole
        from datetime import datetime
        
        # Extract sources, accuracy, and metadata from the message
        sources = message.get("sources", [])
        accuracy = message.get("accuracy")
        extra_metadata = message.get("metadata", {})
        
        # Build full metadata including sources and accuracy for database storage
        full_metadata = {
            **(extra_metadata or {}),
            "sources": sources if sources else [],
            "accuracy": accuracy
        }
        
        chat_message = ChatMessage(
            id=message.get("id", str(uuid.uuid4())),
            role=MessageRole.USER if message.get("role") == "user" else MessageRole.ASSISTANT,
            content=message.get("content", ""),
            timestamp=datetime.now(),
            session_id=session_id
        )
        
        # Get or create session
        session = await chat_service.get_session(session_id)
        if not session:
            session = await chat_service.create_session()
            session.id = session_id
            # 세션 생성 시간이 없으면 현재 시간으로 설정
            if not hasattr(session, 'created_at') or not session.created_at:
                session.created_at = datetime.now()
            if not hasattr(session, 'updated_at') or not session.updated_at:
                session.updated_at = datetime.now()
        
        # Add message to session in memory
        session.add_message(chat_message)
        logger.info(f"Added message to session. Session now has {len(session.messages)} messages")
        
        # Save message directly to database without deleting existing messages
        from sqlalchemy import text
        import json
        
        try:
            async with db_service.get_session() as db_session:
                # Ensure session exists
                await db_session.execute(
                    text("""
                        INSERT INTO chat_sessions (session_id, created_at, updated_at)
                        VALUES (:session_id, :created_at, :updated_at)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET updated_at = :updated_at
                    """),
                    {
                        "session_id": session_id,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at
                    }
                )
                
                # Insert message only if it doesn't exist (by id) - cast string UUID to UUID type
                # Include sources and accuracy in metadata for proper restoration
                metadata_json = json.dumps(full_metadata)
                logger.info(f"Attempting to save message {chat_message.id} for session {session_id} with sources={len(sources)}, accuracy={accuracy is not None}")
                await db_session.execute(
                    text("""
                        INSERT INTO chat_messages 
                        (id, session_id, role, content, metadata, created_at)
                        VALUES (CAST(:id AS UUID), :session_id, :role, :content, :metadata, :created_at)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": chat_message.id,
                        "session_id": session_id,
                        "role": chat_message.role.value,
                        "content": chat_message.content,
                        "metadata": metadata_json,
                        "created_at": chat_message.timestamp
                    }
                )
                
                await db_session.commit()
                logger.info(f"Message {chat_message.id} saved to database for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save message to database: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")
        
        return {"success": True, "message": "Message saved successfully"}
        
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/message")
async def send_message(request: MessageRequest):
    """Send a message and get AI response using selected RAG mode"""
    session_id = request.session_id or "default"
    rag_mode = request.rag_mode or "LangChain RAG"
    
    try:
        # Check cache first for faster response
        cached_response = await cache_service.get_chat_response(request.message, rag_mode)
        if cached_response:
            logger.info(f"Cache hit for {rag_mode} query: {request.message[:100]}...")
            
            # Add model info to cached response
            if request.model_type and request.model_type in settings.MODEL_CONFIGS:
                model_config = settings.MODEL_CONFIGS[request.model_type]
                model_name = model_config["model"]
                model_description = model_config["description"]
                model_use_case = model_config["use_case"]
            else:
                model_name = settings.MODEL_NAME
                model_description = settings.MODEL_CONFIGS.get(request.model_type, {}).get("description", f"{request.model_type} 모델")
                model_use_case = settings.MODEL_CONFIGS.get(request.model_type, {}).get("use_case", "일반적인 사용")
            
            ending_message = f"\n\n---\n\n**AI 모델 정보**\n- 모델: {model_name}\n- 모델 타입: {request.model_type}\n- 설명: {model_description}\n- 답변 방식: 캐시된 답변\n- RAG 모드: {rag_mode}\n\n*이 답변이 도움이 되었나요? 추가로 궁금한 점이 있으시면 언제든지 말씀해 주세요!*"
            final_cached_response = cached_response + ending_message
            
            return {
                "success": True,
                "user_message": {
                    "id": str(uuid.uuid4()),
                    "content": request.message,
                    "timestamp": datetime.now().isoformat()
                },
                "assistant_message": {
                    "id": str(uuid.uuid4()),
                    "content": final_cached_response,
                    "timestamp": datetime.now().isoformat()
                },
                "context": [],
                "metadata": {
                    "context_count": 0,
                    "cached": True,
                    "rag_mode": rag_mode
                }
            }
        
        # Use selected RAG mode
        logger.info(f"Processing {rag_mode} query: {request.message[:100]}...")
        
        if rag_mode == "기본 RAG":
            # Use basic RAG service
            result = await rag_service.rag_query(request.message, session_id, custom_params=request.custom_params)
        else:
            # Use LangChain RAG service (default) with selected collection
            result = await langchain_rag_service.rag_query(
                request.message, 
                session_id, 
                request.model_type, 
                collection_names=request.collection_names,
                custom_params=request.custom_params
            )
        
        if not result["success"]:
            # If RAG fails, return error message instead of fallback
            logger.error(f"{rag_mode} failed: {result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": f"죄송합니다. 현재 vector DB에서 관련 정보를 찾을 수 없어 답변을 생성할 수 없습니다. 먼저 관련 문서를 업로드해 주세요. 오류: {result.get('error', 'Unknown error')}",
                "user_message": {
                    "id": str(uuid.uuid4()),
                    "content": request.message,
                    "timestamp": datetime.now().isoformat()
                },
                "assistant_message": None,
                "context": [],
                "metadata": {
                    "context_count": 0,
                    "vector_db_required": True,
                    "rag_mode": rag_mode
                }
            }
        
        # Cache the response for future use
        await cache_service.set_chat_response(request.message, rag_mode, result["response"])
        
        # Add ending message to response with model and RAG info
        model_info = result.get("model_info", {})
        
        # Get model information from settings based on request.model_type
        if request.model_type and request.model_type in settings.MODEL_CONFIGS:
            model_config = settings.MODEL_CONFIGS[request.model_type]
            model_name = model_config["model"]
            model_type = request.model_type
            model_description = model_config["description"]
            model_use_case = model_config["use_case"]
            logger.info(f"Using model from settings: {model_name} (type: {model_type})")
        else:
            model_name = settings.MODEL_NAME
            model_type = request.model_type or "fast"
            model_description = settings.MODEL_CONFIGS.get(model_type, {}).get("description", f"{model_type} 모델")
            model_use_case = settings.MODEL_CONFIGS.get(model_type, {}).get("use_case", "일반적인 사용")
            logger.info(f"Using default model: {model_name} (type: {model_type})")
        
        # Get context information
        context_count = result.get("metadata", {}).get("context_count", 0)
        context_files = result.get("metadata", {}).get("context_files", [])
        
        # Save messages to database
        try:
            from backend.models.chat import ChatMessage, MessageRole
            from sqlalchemy import text
            import json
            
            user_msg_id = str(uuid.uuid4())
            assistant_msg_id = str(uuid.uuid4())
            
            # Prepare assistant message content with ending
            ending_message = f"\n\n---\n\n**AI 모델 정보**\n- 모델: {model_name}\n- 모델 타입: {model_type}\n- 설명: {model_description}\n- 답변 방식: RAG 기반\n- RAG 모드: {rag_mode}\n\n*이 답변이 도움이 되었나요? 추가로 궁금한 점이 있으시면 언제든지 말씀해 주세요!*"
            assistant_content = result["response"] + ending_message
            
            async with db_service.get_session() as db_session:
                # Ensure session exists
                await db_session.execute(
                    text("""
                        INSERT INTO chat_sessions (session_id, created_at, updated_at)
                        VALUES (:session_id, :created_at, :updated_at)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET updated_at = :updated_at
                    """),
                    {
                        "session_id": session_id,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                )
                
                # Save user message - cast string UUID to UUID type
                logger.info(f"Attempting to save user message {user_msg_id} for session {session_id}")
                await db_session.execute(
                    text("""
                        INSERT INTO chat_messages 
                        (id, session_id, role, content, metadata, created_at)
                        VALUES (CAST(:id AS UUID), :session_id, :role, :content, :metadata, :created_at)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": user_msg_id,
                        "session_id": session_id,
                        "role": "user",
                        "content": request.message,
                        "metadata": json.dumps({}),
                        "created_at": datetime.now()
                    }
                )
                
                # Save assistant message - cast string UUID to UUID type
                logger.info(f"Attempting to save assistant message {assistant_msg_id} for session {session_id}")
                
                # model_info 생성 (저장용)
                model_info_dict = {
                    "모델": model_name,
                    "모델 타입": model_type,
                    "설명": model_description,
                    "답변 방식": "RAG 기반" if context_count > 0 else "기본 모델",
                    "RAG 모드": rag_mode
                }
                
                # sources와 accuracy 정보 준비 (나중에 생성되므로 여기서는 빈 값으로 설정)
                # 실제 sources와 accuracy는 응답 생성 후에 설정됨
                similarity_scores = result.get("metadata", {}).get("similarity_scores", [])
                context_sources = result.get("context", [])
                
                # sources 데이터 생성
                sources_data = []
                if context_sources:
                    for i, doc in enumerate(context_sources):
                        sources_data.append({
                            "filename": doc.get("filename") or doc.get("metadata", {}).get("filename") or doc.get("metadata", {}).get("file_name") or "Unknown",
                            "similarity_score": doc.get("similarity") or (similarity_scores[i] if i < len(similarity_scores) else 0.0),
                            "content_preview": doc.get("content_preview") or doc.get("content", "")[:200] or "",
                            "document_id": doc.get("id") or doc.get("document_id") or ""
                        })
                
                # accuracy 데이터 생성
                accuracy_data = None
                if context_count > 0 or similarity_scores:
                    avg_similarity = (sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0)
                    accuracy_data = {
                        "confidence_score": avg_similarity,
                        "context_count": context_count,
                        "avg_similarity": avg_similarity,
                        "fallback_used": result.get("metadata", {}).get("fallback_mode", False)
                    }
                
                await db_session.execute(
                    text("""
                        INSERT INTO chat_messages 
                        (id, session_id, role, content, metadata, created_at)
                        VALUES (CAST(:id AS UUID), :session_id, :role, :content, :metadata, :created_at)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": assistant_msg_id,
                        "session_id": session_id,
                        "role": "assistant",
                        "content": assistant_content,
                        "metadata": json.dumps({
                            "model_type": model_type,
                            "model_name": model_name,
                            "rag_mode": rag_mode,
                            "context_count": context_count,
                            "context_files": context_files,
                            "model_info": model_info_dict,
                            "sources": sources_data,
                            "accuracy": accuracy_data
                        }),
                        "created_at": datetime.now()
                    }
                )
                
                await db_session.commit()
                logger.info(f"Messages saved to database for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save messages to database: {e}")
            # Continue even if save fails
        similarity_scores = result.get("metadata", {}).get("similarity_scores", [])
        context_sources = result.get("context", [])
        
        rag_status = "RAG 기반" if context_count > 0 else "기본 모델"
        fallback_used = result.get("metadata", {}).get("fallback_mode", False)
        
        if fallback_used:
            rag_status = "기본 모델 (RAG 컨텍스트 없음)"
        
        # Build source information section
        source_info = ""
        if context_count > 0 and context_sources:
            source_info = "\n\n**📚 참고 문서 정보**\n"
            for i, source in enumerate(context_sources):
                filename = source.get("filename", f"문서 {i+1}")
                similarity = source.get("similarity", 0)
                similarity_percent = similarity * 100
                collection = source.get("collection", "Unknown")
                
                # Add source details
                source_info += f"- **{filename}** (정확도: {similarity_percent:.1f}%)\n"
                if collection != "Unknown":
                    source_info += f"  - 컬렉션: {collection}\n"
                if source.get("page_number"):
                    source_info += f"  - 페이지: {source.get('page_number')}\n"
                if source.get("upload_date"):
                    source_info += f"  - 업로드: {source.get('upload_date')}\n"
                source_info += "\n"
            
            # Add average accuracy
            if similarity_scores:
                avg_accuracy = sum(similarity_scores) / len(similarity_scores) * 100
                source_info += f"**평균 정확도: {avg_accuracy:.1f}%**\n"
        else:
            source_info = "\n\n**📚 참고 문서 정보**\n- 참고한 문서가 없습니다. (기본 모델 응답)\n"
        
        ending_message = f"\n\n---\n\n**AI 모델 정보**\n- 모델: {model_name}\n- 모델 타입: {model_type}\n- 설명: {model_description}\n- 답변 방식: {rag_status}\n- RAG 모드: {rag_mode}{source_info}\n*이 답변이 도움이 되었나요? 추가로 궁금한 점이 있으시면 언제든지 말씀해 주세요!*"
        final_response = result["response"] + ending_message
        
        # sources 정보 생성
        sources_data = []
        if context_sources:
            # context_files에서 filename 목록 가져오기 (fallback용)
            context_files_list = result.get("metadata", {}).get("context_files", [])
            
            for i, doc in enumerate(context_sources):
                # filename 추출: 여러 소스에서 시도
                filename = (
                    doc.get("filename") or 
                    doc.get("metadata", {}).get("filename") or 
                    doc.get("metadata", {}).get("file_name") or
                    (context_files_list[i] if i < len(context_files_list) else None) or
                    f"문서 {i+1}"
                )
                
                # "Unknown"이면 더 나은 fallback 사용
                if filename == "Unknown":
                    filename = f"문서 {i+1}"
                
                similarity = doc.get("similarity", similarity_scores[i] if i < len(similarity_scores) else 0)
                content_preview = doc.get("content_preview", doc.get("content", "")[:200] + "...")
                document_id = doc.get("id", doc.get("document_id", ""))
                
                sources_data.append({
                    "filename": filename,
                    "similarity_score": similarity,
                    "content_preview": content_preview,
                    "document_id": document_id
                })
        
        # accuracy 정보 생성
        metadata = result.get("metadata", {})
        avg_similarity = metadata.get("similarity", metadata.get("avg_similarity", 
            (sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0)))
        
        accuracy_data = None
        if context_count > 0 or similarity_scores:
            accuracy_data = {
                "confidence_score": avg_similarity,
                "context_count": context_count,
                "avg_similarity": avg_similarity,
                "fallback_used": fallback_used
            }
        
        # model_info 생성
        model_info_dict = {
            "모델": model_name,
            "모델 타입": model_type,
            "설명": model_description,
            "답변 방식": rag_status,
            "RAG 모드": rag_mode
        }
        
        # Format response for frontend (use the same IDs that were saved)
        return {
            "success": True,
            "user_message": {
                "id": user_msg_id,
                "content": request.message,
                "timestamp": datetime.now().isoformat()
            },
            "assistant_message": {
                "id": assistant_msg_id,
                "content": final_response,
                "timestamp": datetime.now().isoformat(),
                "sources": sources_data,
                "accuracy": accuracy_data,
                "metadata": {
                    **metadata,
                    "model_info": model_info_dict
                }
            },
            "context": result.get("context", []),
            "metadata": result.get("metadata", {})
        }
        
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def save_assistant_message_background(
    session_id: str,
    assistant_msg_id: str,
    final_response_text: str,
    metadata_json: str,
    model_type: str = None,
    model_name: str = None,
    rag_mode: str = None,
    context_count: int = 0,
    context_files: list = None
):
    """Save assistant message to database in background"""
    try:
        from sqlalchemy import text
        
        print(f"[DEBUG] save_assistant_message_background called for session {session_id}")
        print(f"[DEBUG] assistant_msg_id: {assistant_msg_id}")
        print(f"[DEBUG] content length: {len(final_response_text) if final_response_text else 0}")
        logger.info(f"Background: Attempting to save assistant message {assistant_msg_id} for session {session_id}")
        
        async with db_service.get_session() as db_session:
            # Update session timestamp
            await db_session.execute(
                text("""
                    UPDATE chat_sessions 
                    SET updated_at = :updated_at
                    WHERE session_id = :session_id
                """),
                {
                    "session_id": session_id,
                    "updated_at": datetime.now()
                }
            )
            
            # Save assistant message with provided metadata
            await db_session.execute(
                text("""
                    INSERT INTO chat_messages 
                    (id, session_id, role, content, metadata, created_at)
                    VALUES (CAST(:id AS UUID), :session_id, :role, :content, :metadata, :created_at)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": assistant_msg_id,
                    "session_id": session_id,
                    "role": "assistant",
                    "content": final_response_text,
                    "metadata": metadata_json,
                    "created_at": datetime.now()
                }
            )
            
            await db_session.commit()
            
            # Verify message was saved
            verify_result = await db_session.execute(
                text("SELECT COUNT(*) FROM chat_messages WHERE id = CAST(:id AS UUID)"),
                {"id": assistant_msg_id}
            )
            count = verify_result.scalar()
            if count > 0:
                logger.info(f"Background: Assistant message {assistant_msg_id} successfully saved to database for session {session_id}")
            else:
                logger.warning(f"Background: Assistant message {assistant_msg_id} was not saved (possibly conflict)")
    except Exception as save_error:
        logger.error(f"Background: Failed to save assistant message to database: {save_error}", exc_info=True)

@app.post("/api/chat/stream")
async def stream_chat(request: ChatRequest, background_tasks: BackgroundTasks, current_user: User = Depends(auth_controller.get_current_user)):
    """Stream chat response using selected RAG mode with Server-Sent Events"""
    try:
        session_id = request.session_id or "default"
        rag_mode = request.rag_mode or "LangChain RAG"
        # 현재 사용자 ID 가져오기 (chat_service.get_all_sessions와 일관성 유지)
        user_id = current_user.id if current_user else "default"
        
        # Save user message before streaming starts
        user_msg_id = None
        try:
            from sqlalchemy import text
            import json as json_lib
            user_msg_id = str(uuid.uuid4())
            
            logger.info(f"Attempting to save user message {user_msg_id} for session {session_id}, user {user_id}")
            
            async with db_service.get_session() as db_session:
                # Ensure session exists with user_id
                await db_session.execute(
                    text("""
                        INSERT INTO chat_sessions (session_id, user_id, created_at, updated_at)
                        VALUES (:session_id, :user_id, :created_at, :updated_at)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET updated_at = :updated_at, user_id = COALESCE(chat_sessions.user_id, :user_id)
                    """),
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                )
                
                # Save user message - cast string UUID to UUID type
                await db_session.execute(
                    text("""
                        INSERT INTO chat_messages 
                        (id, session_id, role, content, metadata, created_at)
                        VALUES (CAST(:id AS UUID), :session_id, :role, :content, :metadata, :created_at)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": user_msg_id,
                        "session_id": session_id,
                        "role": "user",
                        "content": request.message,
                        "metadata": json_lib.dumps({}),
                        "created_at": datetime.now()
                    }
                )
                
                await db_session.commit()
                
                # Verify message was saved
                verify_result = await db_session.execute(
                    text("SELECT COUNT(*) FROM chat_messages WHERE id = CAST(:id AS UUID)"),
                    {"id": user_msg_id}
                )
                count = verify_result.scalar()
                if count > 0:
                    logger.info(f"User message {user_msg_id} successfully saved to database for session {session_id}")
                else:
                    logger.warning(f"User message {user_msg_id} was not saved (possibly conflict)")
        except Exception as save_error:
            logger.error(f"Failed to save user message to database: {save_error}", exc_info=True)
        
        # Variables to store response data for saving after streaming
        response_data = {
            "final_text": None,
            "model_type": None,
            "model_name": None,
            "rag_mode": rag_mode,
            "context_count": 0,
            "context_files": [],
            "detailed_sources": [],
            "accuracy_info": None,
            "model_description": "",
            "rag_status": "",
            "should_save": False  # Flag to indicate if assistant message should be saved
        }
        
        async def generate_response():
            try:
                # Use selected RAG mode
                logger.info(f"Processing {rag_mode} stream query: {request.message[:100]}...")
                
                if rag_mode == "기본 RAG":
                    # Use basic RAG service
                    result = await rag_service.rag_query(request.message, session_id)
                else:
                    # Use LangChain RAG service (default)
                    result = await langchain_rag_service.rag_query(request.message, session_id, request.model_type, request.collection_names)
                
                if result["success"] and result.get("response"):
                    # Stream the response
                    response_text = result["response"]
                    
                    # Send context information first
                    metadata = result.get("metadata", {})
                    similarity_scores = metadata.get("similarity_scores", [])
                    context_sources = result.get("context", [])
                    context_count = len(context_sources)
                    avg_similarity = metadata.get("similarity", metadata.get("avg_similarity", 
                        (sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0)))
                    
                    # 메시지 저장을 위해 외부 변수 선언
                    detailed_sources_for_save = []
                    accuracy_info_for_save = None
                    
                    if context_sources:
                        # sources 정보 생성
                        detailed_sources = []
                        # context_files에서 filename 목록 가져오기 (fallback용)
                        context_files_list = metadata.get("context_files", [])
                        
                        for i, doc in enumerate(context_sources):
                            # filename 추출: 여러 소스에서 시도
                            filename = (
                                doc.get("filename") or 
                                doc.get("metadata", {}).get("filename") or 
                                doc.get("metadata", {}).get("file_name") or
                                (context_files_list[i] if i < len(context_files_list) else None) or
                                f"문서 {i+1}"
                            )
                            
                            # "Unknown"이면 더 나은 fallback 사용
                            if filename == "Unknown":
                                filename = f"문서 {i+1}"
                            
                            similarity = doc.get("similarity", similarity_scores[i] if i < len(similarity_scores) else 0)
                            content_preview = doc.get("content_preview", doc.get("content", "")[:200] + "...")
                            document_id = doc.get("id", doc.get("document_id", ""))
                            
                            detailed_sources.append({
                                "filename": filename,
                                "similarity_score": similarity,
                                "content_preview": content_preview,
                                "document_id": document_id
                            })
                        
                        context_info = {
                            "type": "context",
                            "sources": [doc.get("filename") or doc.get("metadata", {}).get("filename") or doc.get("metadata", {}).get("file_name") or f"문서 {i+1}" for i, doc in enumerate(context_sources)],
                            "context_files": metadata.get("context_files", []),
                            "source_collection": metadata.get("source_collection", "documents"),
                            "source_collections": metadata.get("source_collections", []),
                            "collections_used": metadata.get("collections_used", []),
                            "multi_collection": metadata.get("multi_collection", False),
                            "context_count": context_count,
                            "detailed_sources": detailed_sources,
                            "similarity_scores": similarity_scores,
                            "similarity": avg_similarity,
                            "accuracy": {
                                "confidence_score": avg_similarity,
                                "context_count": context_count,
                                "avg_similarity": avg_similarity,
                                "fallback_used": metadata.get("fallback_mode", False)
                            } if context_count > 0 or similarity_scores else None
                        }
                        
                        # 메시지 저장을 위해 정보 저장
                        detailed_sources_for_save = detailed_sources
                        accuracy_info_for_save = context_info.get("accuracy")
                        
                        yield {
                            "event": "context",
                            "data": json.dumps(context_info)
                        }
                    
                    # Add ending message to response with model and RAG info
                    model_info = result.get("model_info", {})
                    
                    # Get model information from settings based on request.model_type
                    if request.model_type and request.model_type in settings.MODEL_CONFIGS:
                        model_config = settings.MODEL_CONFIGS[request.model_type]
                        model_name = model_config["model"]
                        model_type = request.model_type
                        model_description = model_config["description"]
                        model_use_case = model_config["use_case"]
                    else:
                        model_name = settings.MODEL_NAME
                        model_type = request.model_type or "fast"
                        model_description = settings.MODEL_CONFIGS.get(model_type, {}).get("description", f"{model_type} 모델")
                        model_use_case = settings.MODEL_CONFIGS.get(model_type, {}).get("use_case", "일반적인 사용")
                    
                    rag_status = "RAG 기반" if result.get("metadata", {}).get("context_count", 0) > 0 else "기본 모델"
                    fallback_used = result.get("metadata", {}).get("fallback_mode", False)
                    
                    if fallback_used:
                        rag_status = "기본 모델 (RAG 컨텍스트 없음)"
                    
                    ending_message = f"\n\n---\n\n**AI 모델 정보**\n- 모델: {model_name}\n- 모델 타입: {model_type}\n- 설명: {model_description}\n- 답변 방식: {rag_status}\n- RAG 모드: {rag_mode}\n\n*이 답변이 도움이 되었나요? 추가로 궁금한 점이 있으시면 언제든지 말씀해 주세요!*"
                    final_response_text = response_text + ending_message
                    
                    # Store response data for saving after streaming
                    response_data["final_text"] = final_response_text
                    response_data["model_type"] = model_type
                    response_data["model_name"] = model_name
                    response_data["context_count"] = len(result.get("context", []))
                    response_data["context_files"] = result.get("metadata", {}).get("context_files", [])
                    
                    # Stream the response text with optimized chunking
                    chunk_size = 8  # Slightly larger chunks for better performance
                    for i in range(0, len(final_response_text), chunk_size):
                        chunk = final_response_text[i:i+chunk_size]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False,
                                "type": "chunk"
                            })
                        }
                        # Dynamic delay based on chunk size for optimal performance
                        delay = 0.005 if len(chunk) > 5 else 0.01
                        await asyncio.sleep(delay)
                    
                    # Create model_info for metadata
                    model_info_dict = {
                        "모델": model_name,
                        "모델 타입": model_type,
                        "설명": model_description,
                        "답변 방식": rag_status,
                        "RAG 모드": rag_mode
                    }
                    
                    # Save assistant message SYNCHRONOUSLY before sending completion signal
                    import json as json_lib
                    
                    assistant_msg_id = str(uuid.uuid4())
                    # Use response_data values which were set earlier
                    saved_context_count = response_data.get("context_count", 0)
                    saved_context_files = response_data.get("context_files", [])
                    
                    message_metadata = {
                        "model_type": model_type,
                        "model_name": model_name,
                        "rag_mode": rag_mode,
                        "context_count": saved_context_count,
                        "context_files": saved_context_files,
                        "sources": detailed_sources_for_save,
                        "accuracy": accuracy_info_for_save,
                        "model_info": model_info_dict
                    }
                    
                    # Save synchronously using await
                    await save_assistant_message_background(
                        session_id,
                        assistant_msg_id,
                        final_response_text,
                        json_lib.dumps(message_metadata),
                        model_type,
                        model_name,
                        rag_mode,
                        saved_context_count,
                        saved_context_files
                    )
                    logger.info(f"Assistant message {assistant_msg_id} saved for session {session_id}")
                    
                    # Send completion signal with model_info
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True,
                            "type": "completion",
                            "model_info": model_info_dict
                        })
                    }
                else:
                    # If RAG fails, send error message
                    error_message = f"죄송합니다. 현재 vector DB에서 관련 정보를 찾을 수 없어 답변을 생성할 수 없습니다. 먼저 관련 문서를 업로드해 주세요. 오류: {result.get('error', 'Unknown error')}"
                    
                    # Stream error message with same chunking as regular response
                    chunk_size = 5
                    for i in range(0, len(error_message), chunk_size):
                        chunk = error_message[i:i+chunk_size]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False,
                                "type": "chunk"
                            })
                        }
                        await asyncio.sleep(0.01)  # 스트리밍 지연 70% 감소 (30ms → 10ms)
                    
                    # Create model_info for metadata
                    model_info_dict = {
                        "모델": model_name,
                        "모델 타입": model_type,
                        "설명": model_description,
                        "답변 방식": rag_status,
                        "RAG 모드": rag_mode
                    }
                    
                    # Send completion signal with model_info
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True,
                            "type": "completion",
                            "model_info": model_info_dict
                        })
                    }
                    
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": str(e),
                        "finished": True
                    })
                }
            finally:
                # Save assistant message after streaming completes (or fails)
                if response_data.get("should_save") and response_data.get("final_text"):
                    try:
                        from sqlalchemy import text
                        import json as json_lib
                        
                        assistant_msg_id = str(uuid.uuid4())
                        logger.info(f"Finally block: Saving assistant message {assistant_msg_id} for session {session_id}")
                        
                        async with db_service.get_session() as db_session:
                            # Update session timestamp
                            await db_session.execute(
                                text("""
                                    UPDATE chat_sessions 
                                    SET updated_at = :updated_at
                                    WHERE session_id = :session_id
                                """),
                                {
                                    "session_id": session_id,
                                    "updated_at": datetime.now()
                                }
                            )
                            
                            # Save assistant message with sources and accuracy
                            message_metadata = {
                                "model_type": response_data.get("model_type"),
                                "model_name": response_data.get("model_name"),
                                "rag_mode": response_data.get("rag_mode"),
                                "context_count": response_data.get("context_count", 0),
                                "context_files": response_data.get("context_files", []),
                                "sources": response_data.get("detailed_sources", []),
                                "accuracy": response_data.get("accuracy_info"),
                                "model_info": {
                                    "모델": response_data.get("model_name"),
                                    "모델 타입": response_data.get("model_type"),
                                    "설명": response_data.get("model_description", ""),
                                    "답변 방식": response_data.get("rag_status", ""),
                                    "RAG 모드": response_data.get("rag_mode")
                                }
                            }
                            
                            await db_session.execute(
                                text("""
                                    INSERT INTO chat_messages 
                                    (id, session_id, role, content, metadata, created_at)
                                    VALUES (CAST(:id AS UUID), :session_id, :role, :content, :metadata, :created_at)
                                    ON CONFLICT (id) DO NOTHING
                                """),
                                {
                                    "id": assistant_msg_id,
                                    "session_id": session_id,
                                    "role": "assistant",
                                    "content": response_data.get("final_text", ""),
                                    "metadata": json_lib.dumps(message_metadata),
                                    "created_at": datetime.now()
                                }
                            )
                            
                            await db_session.commit()
                            
                            # Verify message was saved
                            verify_result = await db_session.execute(
                                text("SELECT COUNT(*) FROM chat_messages WHERE id = CAST(:id AS UUID)"),
                                {"id": assistant_msg_id}
                            )
                            count = verify_result.scalar()
                            if count > 0:
                                logger.info(f"Finally block: Assistant message {assistant_msg_id} saved successfully for session {session_id}")
                            else:
                                logger.warning(f"Finally block: Assistant message {assistant_msg_id} was not saved (possibly conflict)")
                    except Exception as save_error:
                        logger.error(f"Finally block: Failed to save assistant message: {save_error}", exc_info=True)
        
        return EventSourceResponse(generate_response())
        
    except Exception as e:
        logger.error(f"Failed to start streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream/langchain")
async def stream_chat_langchain(request: ChatRequest):
    """Stream chat response using selected RAG mode with Server-Sent Events"""
    try:
        async def generate_response():
            try:
                # Use selected RAG mode
                rag_mode = request.rag_mode or "LangChain RAG"
                logger.info(f"Processing {rag_mode} stream query: {request.message[:100]}...")
                
                if rag_mode == "기본 RAG":
                    # Use basic RAG service
                    result = await rag_service.rag_query(request.message, request.session_id)
                else:
                    # Use LangChain RAG service (default)
                    result = await langchain_rag_service.rag_query(request.message, request.session_id, request.model_type, request.collection_names)
                
                if result["success"] and result.get("response"):
                    response_text = result["response"]
                    
                    # Send context information first
                    metadata = result.get("metadata", {})
                    similarity_scores = metadata.get("similarity_scores", [])
                    context_sources = result.get("context", [])
                    context_count = len(context_sources)
                    avg_similarity = metadata.get("similarity", metadata.get("avg_similarity", 
                        (sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0)))
                    
                    if context_sources:
                        # sources 정보 생성
                        detailed_sources = []
                        # context_files에서 filename 목록 가져오기 (fallback용)
                        context_files_list = metadata.get("context_files", [])
                        
                        for i, doc in enumerate(context_sources):
                            # filename 추출: 여러 소스에서 시도
                            filename = (
                                doc.get("filename") or 
                                doc.get("metadata", {}).get("filename") or 
                                doc.get("metadata", {}).get("file_name") or
                                (context_files_list[i] if i < len(context_files_list) else None) or
                                f"문서 {i+1}"
                            )
                            
                            # "Unknown"이면 더 나은 fallback 사용
                            if filename == "Unknown":
                                filename = f"문서 {i+1}"
                            
                            similarity = doc.get("similarity", similarity_scores[i] if i < len(similarity_scores) else 0)
                            content_preview = doc.get("content_preview", doc.get("content", "")[:200] + "...")
                            document_id = doc.get("id", doc.get("document_id", ""))
                            
                            detailed_sources.append({
                                "filename": filename,
                                "similarity_score": similarity,
                                "content_preview": content_preview,
                                "document_id": document_id
                            })
                        
                        context_info = {
                            "type": "context",
                            "sources": [doc.get("filename") or doc.get("metadata", {}).get("filename") or doc.get("metadata", {}).get("file_name") or f"문서 {i+1}" for i, doc in enumerate(context_sources)],
                            "context_files": metadata.get("context_files", []),
                            "source_collection": metadata.get("source_collection", "documents"),
                            "source_collections": metadata.get("source_collections", []),
                            "collections_used": metadata.get("collections_used", []),
                            "multi_collection": metadata.get("multi_collection", False),
                            "context_count": context_count,
                            "detailed_sources": detailed_sources,
                            "similarity_scores": similarity_scores,
                            "similarity": avg_similarity,
                            "accuracy": {
                                "confidence_score": avg_similarity,
                                "context_count": context_count,
                                "avg_similarity": avg_similarity,
                                "fallback_used": metadata.get("fallback_mode", False)
                            } if context_count > 0 or similarity_scores else None
                        }
                        yield {
                            "event": "context",
                            "data": json.dumps(context_info)
                        }
                    
                    # Add ending message to response with model and RAG info
                    model_info = result.get("model_info", {})
                    
                    # Get model information from settings based on request.model_type
                    if request.model_type and request.model_type in settings.MODEL_CONFIGS:
                        model_config = settings.MODEL_CONFIGS[request.model_type]
                        model_name = model_config["model"]
                        model_type = request.model_type
                        model_description = model_config["description"]
                        model_use_case = model_config["use_case"]
                    else:
                        model_name = settings.MODEL_NAME
                        model_type = request.model_type or "fast"
                        model_description = settings.MODEL_CONFIGS.get(model_type, {}).get("description", f"{model_type} 모델")
                        model_use_case = settings.MODEL_CONFIGS.get(model_type, {}).get("use_case", "일반적인 사용")
                    
                    rag_status = "RAG 기반" if result.get("metadata", {}).get("context_count", 0) > 0 else "기본 모델"
                    fallback_used = result.get("metadata", {}).get("fallback_mode", False)
                    
                    if fallback_used:
                        rag_status = "기본 모델 (RAG 컨텍스트 없음)"
                    
                    ending_message = f"\n\n---\n\n**AI 모델 정보**\n- 모델: {model_name}\n- 모델 타입: {model_type}\n- 설명: {model_description}\n- 답변 방식: {rag_status}\n- RAG 모드: {rag_mode}\n\n*이 답변이 도움이 되었나요? 추가로 궁금한 점이 있으시면 언제든지 말씀해 주세요!*"
                    final_response_text = response_text + ending_message
                    
                    # Stream the response text with optimized chunking
                    chunk_size = 8  # Slightly larger chunks for better performance
                    for i in range(0, len(final_response_text), chunk_size):
                        chunk = final_response_text[i:i+chunk_size]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False,
                                "type": "chunk"
                            })
                        }
                        # Dynamic delay based on chunk size for optimal performance
                        delay = 0.005 if len(chunk) > 5 else 0.01
                        await asyncio.sleep(delay)
                    
                    # Create model_info for metadata
                    model_info_dict = {
                        "모델": model_name,
                        "모델 타입": model_type,
                        "설명": model_description,
                        "답변 방식": rag_status,
                        "RAG 모드": rag_mode
                    }
                    
                    # Send completion signal with model_info
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True,
                            "type": "completion",
                            "model_info": model_info_dict
                        })
                    }
                else:
                    # If RAG fails, send error message
                    error_message = f"죄송합니다. 현재 vector DB에서 관련 정보를 찾을 수 없어 답변을 생성할 수 없습니다. 먼저 관련 문서를 업로드해 주세요. 오류: {result.get('error', 'Unknown error')}"
                    
                    # Stream error message with same chunking as regular response
                    chunk_size = 5
                    for i in range(0, len(error_message), chunk_size):
                        chunk = error_message[i:i+chunk_size]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False,
                                "type": "chunk"
                            })
                        }
                        await asyncio.sleep(0.01)  # 스트리밍 지연 70% 감소 (30ms → 10ms)
                    
                    # Create model_info for metadata
                    model_info_dict = {
                        "모델": model_name,
                        "모델 타입": model_type,
                        "설명": model_description,
                        "답변 방식": rag_status,
                        "RAG 모드": rag_mode
                    }
                    
                    # Send completion signal with model_info
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True,
                            "type": "completion",
                            "model_info": model_info_dict
                        })
                    }
                    
            except Exception as e:
                logger.error(f"LangChain streaming error: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": str(e),
                        "finished": True
                    })
                }
        
        return EventSourceResponse(generate_response())
        
    except Exception as e:
        logger.error(f"Failed to start LangChain streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: Optional[int] = None):
    """Get chat history for a session"""
    try:
        messages = await chat_service.get_chat_history(session_id, limit)
        return {
            "success": True,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "sources": [
                        {
                            "filename": s.filename, 
                            "similarity_score": s.similarity_score,
                            "content_preview": s.content_preview,
                            "document_id": s.document_id
                        } 
                        for s in msg.sources
                    ] if msg.sources else [],
                    "accuracy": {
                        "confidence_score": msg.accuracy.confidence_score,
                        "context_count": msg.accuracy.context_count,
                        "avg_similarity": msg.accuracy.avg_similarity,
                        "fallback_used": msg.accuracy.fallback_used
                    } if msg.accuracy else None,
                    "metadata": msg.metadata
                }
                for msg in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/chat/sessions")
async def get_sessions(current_user: User = Depends(auth_controller.get_current_user)):
    """Get all session IDs"""
    try:
        session_ids = await chat_service.get_all_sessions(current_user)
        return {
            "success": True,
            "sessions": session_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/session/{session_id}/exists")
async def check_session_exists(session_id: str):
    """Check if a session exists without loading all sessions"""
    try:
        exists = await chat_service.session_exists(session_id)
        return {
            "success": True,
            "exists": exists
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session"""
    try:
        success = await chat_service.clear_session(session_id)
        return {
            "success": success,
            "message": "Session cleared successfully" if success else "Failed to clear session"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/session/{session_id}/delete")
async def delete_session(session_id: str):
    """Delete a chat session completely"""
    try:
        success = await chat_service.delete_session(session_id)
        return {
            "success": success,
            "message": "Session deleted successfully" if success else "Failed to delete session"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/sessions/all")
async def clear_all_sessions():
    """Clear all sessions except default"""
    try:
        cleared_sessions = await chat_service.clear_all_sessions()
        return {
            "success": True,
            "cleared_sessions": cleared_sessions,
            "message": f"Cleared {len(cleared_sessions)} sessions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Get session statistics"""
    try:
        stats = await chat_service.get_session_stats(session_id)
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat Session Management APIs
@app.post("/api/chat/sessions/create")
async def create_chat_session(request: dict):
    """Create a new chat session with title"""
    try:
        session_id = request.get("session_id")
        user_id = request.get("user_id", "default")
        title = request.get("title", "새 대화")
        
        result = await chat_service.create_chat_session(session_id, user_id, title)
        return {
            "success": True,
            "session": result,
            "message": "Chat session created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/chat/sessions/{session_id}/title")
async def update_session_title(session_id: str, request: UpdateSessionTitleRequest):
    """Update chat session title"""
    try:
        if not request.title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        result = await chat_service.update_session_title(session_id, request.title, request.user_id)
        return {
            "success": result,
            "message": "Session title updated successfully" if result else "Failed to update session title"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/chat/sessions/{session_id}/description")
async def update_session_description(session_id: str, request: UpdateSessionDescriptionRequest):
    """Update chat session description"""
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        result = await chat_service.update_session_description(session_id, request.description or "", request.user_id)
        
        if result:
            return {
                "success": True,
                "message": "Session description updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update session description")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session description: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update session description: {str(e)}")

@app.post("/api/chat/sessions/{session_id}/generate-title")
async def generate_session_title(session_id: str, request: dict):
    """Generate session title based on first question"""
    try:
        first_question = request.get("first_question", "")
        user_id = request.get("user_id", "default")
        
        if not first_question:
            raise HTTPException(status_code=400, detail="First question is required")
        
        # Generate title using prompt service
        from backend.services.prompt_service import prompt_service
        generated_title = prompt_service.generate_session_title(first_question)
        
        # Update session title in database
        result = await chat_service.update_session_title(session_id, generated_title, user_id)
        
        return {
            "success": result,
            "title": generated_title,
            "message": "Session title generated and updated successfully" if result else "Failed to update session title"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/sessions/user/{user_id}")
async def get_user_sessions(user_id: str):
    """Get all sessions for a user"""
    try:
        sessions = await chat_service.get_user_sessions(user_id)
        return {
            "success": True,
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        return {
            "success": False,
            "sessions": [],
            "error": str(e)
        }

@app.get("/api/chat/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        session_info = await chat_service.get_session_info(session_id)
        return {
            "success": True,
            "session": session_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session from database"""
    try:
        result = await chat_service.delete_chat_session(session_id)
        return {
            "success": result,
            "message": "Session deleted successfully" if result else "Failed to delete session"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Document management endpoints
@app.post("/api/documents")
async def add_document(request: DocumentRequest):
    """Add document to knowledge base"""
    try:
        doc_id = await rag_service.add_document(request.content, request.metadata)
        return {
            "success": True,
            "document_id": doc_id,
            "message": "Document added successfully"
        }
    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# LangChain RAG endpoints
@app.post("/api/langchain/documents")
async def add_document_langchain(request: DocumentRequest):
    """Add document to LangChain knowledge base"""
    try:
        doc_id = await langchain_rag_service.add_document(request.content, request.metadata)
        return {
            "success": True,
            "document_id": doc_id,
            "message": "Document added to LangChain knowledge base successfully"
        }
    except Exception as e:
        logger.error(f"Failed to add document to LangChain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langchain/chat/message")
async def langchain_chat_message(request: MessageRequest):
    """Send message using LangChain RAG"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Generate message IDs
        user_message_id = str(uuid.uuid4())
        assistant_message_id = str(uuid.uuid4())
        
        # Create user message
        user_message = {
            "id": user_message_id,
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Use selected RAG mode
        rag_mode = request.rag_mode or "LangChain RAG"
        logger.info(f"Processing {rag_mode} query: {request.message[:100]}...")
        
        if rag_mode == "기본 RAG":
            # Use basic RAG service
            rag_result = await rag_service.rag_query(request.message, request.session_id)
        else:
            # Use LangChain RAG service (default)
            rag_result = await langchain_rag_service.rag_query(request.message, request.session_id, request.model_type)
        
        if rag_result["success"]:
            # Add ending message to response with model and RAG info
            model_info = rag_result.get("model_info", {})
            logger.info(f"Request model_type: {request.model_type}")
            logger.info(f"Request model_type type: {type(request.model_type)}")
            logger.info(f"Request object: {request}")
            logger.info(f"RAG result model_info: {model_info}")
            logger.info(f"Available model configs: {list(settings.MODEL_CONFIGS.keys())}")
            
            # Get model information from settings based on request.model_type
            if request.model_type and request.model_type in settings.MODEL_CONFIGS:
                model_config = settings.MODEL_CONFIGS[request.model_type]
                model_name = model_config["model"]
                model_type = request.model_type
                model_description = model_config["description"]
                model_use_case = model_config["use_case"]
                logger.info(f"Using model from settings: {model_name} (type: {model_type})")
            else:
                model_name = settings.MODEL_NAME
                model_type = request.model_type or "fast"
                model_description = settings.MODEL_CONFIGS.get(model_type, {}).get("description", f"{model_type} 모델")
                model_use_case = settings.MODEL_CONFIGS.get(model_type, {}).get("use_case", "일반적인 사용")
                logger.info(f"Using default model: {model_name} (type: {model_type})")
            
            rag_status = "RAG 기반" if rag_result.get("metadata", {}).get("context_count", 0) > 0 else "기본 모델"
            fallback_used = rag_result.get("metadata", {}).get("fallback_mode", False)
            
            if fallback_used:
                rag_status = "기본 모델 (RAG 컨텍스트 없음)"
            
            ending_message = f"\n\n---\n\n**AI 모델 정보**\n- 모델: {model_name}\n- 모델 타입: {model_type}\n- 설명: {model_description}\n- 답변 방식: {rag_status}\n- RAG 모드: {rag_mode}\n\n*이 답변이 도움이 되었나요? 추가로 궁금한 점이 있으시면 언제든지 말씀해 주세요!*"
            final_response = rag_result["response"] + ending_message
            
            # sources 정보 생성
            sources_data = []
            context_sources = rag_result.get("context", [])
            similarity_scores = rag_result.get("metadata", {}).get("similarity_scores", [])
            context_count = rag_result.get("metadata", {}).get("context_count", 0)
            
            if context_sources:
                # context_files에서 filename 목록 가져오기 (fallback용)
                context_files_list = rag_result.get("metadata", {}).get("context_files", [])
                
                for i, doc in enumerate(context_sources):
                    # filename 추출: 여러 소스에서 시도
                    filename = (
                        doc.get("filename") or 
                        doc.get("metadata", {}).get("filename") or 
                        doc.get("metadata", {}).get("file_name") or
                        (context_files_list[i] if i < len(context_files_list) else None) or
                        f"문서 {i+1}"
                    )
                    
                    # "Unknown"이면 더 나은 fallback 사용
                    if filename == "Unknown":
                        filename = f"문서 {i+1}"
                    
                    similarity = doc.get("similarity", similarity_scores[i] if i < len(similarity_scores) else 0)
                    content_preview = doc.get("content_preview", doc.get("content", "")[:200] + "...")
                    document_id = doc.get("id", doc.get("document_id", ""))
                    
                    sources_data.append({
                        "filename": filename,
                        "similarity_score": similarity,
                        "content_preview": content_preview,
                        "document_id": document_id
                    })
            
            # accuracy 정보 생성
            metadata = rag_result.get("metadata", {})
            avg_similarity = metadata.get("similarity", metadata.get("avg_similarity", 
                (sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0)))
            
            accuracy_data = None
            if context_count > 0 or similarity_scores:
                accuracy_data = {
                    "confidence_score": avg_similarity,
                    "context_count": context_count,
                    "avg_similarity": avg_similarity,
                    "fallback_used": fallback_used
                }
            
            # Create proper model_info
            proper_model_info = {
                "모델": model_name,
                "모델 타입": model_type,
                "설명": model_description,
                "답변 방식": rag_status,
                "RAG 모드": rag_mode
            }
            
            assistant_message = {
                "id": assistant_message_id,
                "content": final_response,
                "timestamp": datetime.now().isoformat(),
                "sources": sources_data,
                "accuracy": accuracy_data,
                "metadata": {
                    **metadata,
                    "model_info": proper_model_info
                }
            }
            
            return {
                "success": True,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "context": rag_result.get("context", []),
                "metadata": rag_result.get("metadata", {}),
                "langchain_mode": True
            }
        else:
            # If RAG fails, return error message
            error_message = f"죄송합니다. 현재 vector DB에서 관련 정보를 찾을 수 없어 답변을 생성할 수 없습니다. 먼저 관련 문서를 업로드해 주세요. 오류: {rag_result.get('error', 'Unknown error')}"
            
            assistant_message = {
                "id": assistant_message_id,
                "content": error_message,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": False,
                "error": error_message,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "context": [],
                "metadata": {
                    "context_count": 0,
                    "vector_db_required": True,
                    "langchain_mode": True
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LangChain chat message failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/langchain/memory/clear")
async def clear_langchain_memory(request: SessionRequest):
    """Clear LangChain conversation memory"""
    try:
        success = await langchain_rag_service.clear_memory(request.session_id)
        return {
            "success": success,
            "message": "Memory cleared successfully" if success else "Failed to clear memory"
        }
    except Exception as e:
        logger.error(f"Failed to clear memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/langchain/memory/state")
async def get_langchain_memory_state():
    """Get LangChain memory state"""
    try:
        memory_state = await langchain_rag_service.get_memory_state()
        return {
            "success": True,
            "memory_state": memory_state
        }
    except Exception as e:
        logger.error(f"Failed to get memory state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document by ID"""
    try:
        document = await vector_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"success": True, "document": document}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete document by ID"""
    try:
        deleted = await vector_service.delete_document(doc_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"success": True, "message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def get_documents(
    request: Request,
    collection_name: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    order_by: Optional[str] = "created_at",  # created_at, updated_at
    order_direction: Optional[str] = "desc"  # asc, desc
):
    """Get document list with filtering and pagination"""
    try:
        # Get current user if authenticated (optional)
        user_id = None
        try:
            if request:
                authorization = request.headers.get("Authorization")
                if authorization and authorization.startswith("Bearer "):
                    token = authorization[7:]
                    user = await auth_service.get_current_user(token)
                    if user and hasattr(user, 'id'):
                        user_id = user.id
        except:
            pass
        
        async with db_service.get_session() as session:
            # Check if user_id column exists in documents table
            try:
                user_id_column_check = await session.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'documents' AND column_name = 'user_id'
                """))
                has_user_id = user_id_column_check.fetchone() is not None
            except:
                has_user_id = False

            # Check if collection is a LangChain collection
            is_langchain_collection = False
            collection_uuid = None
            has_langchain_user_id = False

            if collection_name and collection_name != "documents":
                # Check if it's a LangChain collection
                langchain_collection_result = await session.execute(
                    text("SELECT uuid FROM langchain_pg_collection WHERE name = :collection_name"),
                    {"collection_name": collection_name}
                )
                langchain_collection_row = langchain_collection_result.fetchone()
                if langchain_collection_row:
                    is_langchain_collection = True
                    collection_uuid = str(langchain_collection_row.uuid)
                    
                    # Check if user_id column exists in langchain_pg_collection
                    try:
                        langchain_user_id_check = await session.execute(text("""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name = 'langchain_pg_collection' AND column_name = 'user_id'
                        """))
                        has_langchain_user_id = langchain_user_id_check.fetchone() is not None
                    except:
                        has_langchain_user_id = False
            
            if is_langchain_collection:
                # Query from langchain_pg_embedding table
                # LangChain stores documents as chunks, so we group by filename to show each document as one entry
                
                # Build query conditionally based on whether user_id column exists
                # Build WHERE clause parts
                where_clauses = ["c.name = :collection_name", "(e.cmetadata->>'filename') IS NOT NULL"]
                params = {"collection_name": collection_name}
                
                # Add user filter to WHERE clause if authenticated and user_id column exists
                if user_id and has_langchain_user_id:
                    where_clauses.append("(c.user_id = :user_id OR c.user_id IS NULL)")
                    params["user_id"] = user_id
                
                where_clause = " AND ".join(where_clauses)
                
                if has_langchain_user_id:
                    query = f"""
                        SELECT
                            (e.cmetadata->>'filename') as id,
                            string_agg(e.document, E'\\n\\n--- 청크 구분선 ---\\n\\n') as content,
                            jsonb_build_object(
                                'filename', (e.cmetadata->>'filename'),
                                'file_type', MAX(e.cmetadata->>'file_type'),
                                'chunk_count', COUNT(*),
                                'total_chunks', COUNT(*)
                            ) as metadata,
                            c.name as collection_name,
                            c.user_id::text as user_id,
                            MIN(COALESCE(
                                (e.cmetadata->>'created_at')::timestamp,
                                (e.cmetadata->>'created_date')::timestamp,
                                (e.cmetadata->>'upload_date')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as created_at,
                            MAX(COALESCE(
                                (e.cmetadata->>'updated_at')::timestamp,
                                (e.cmetadata->>'modified_date')::timestamp,
                                (e.cmetadata->>'created_at')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as updated_at,
                            CASE WHEN COUNT(CASE WHEN e.embedding IS NOT NULL THEN 1 END) > 0 THEN true ELSE false END as has_embedding
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE {where_clause}
                        GROUP BY (e.cmetadata->>'filename'), c.name, c.user_id
                    """
                else:
                    query = f"""
                        SELECT
                            (e.cmetadata->>'filename') as id,
                            string_agg(e.document, E'\\n\\n--- 청크 구분선 ---\\n\\n') as content,
                            jsonb_build_object(
                                'filename', (e.cmetadata->>'filename'),
                                'file_type', MAX(e.cmetadata->>'file_type'),
                                'chunk_count', COUNT(*),
                                'total_chunks', COUNT(*)
                            ) as metadata,
                            c.name as collection_name,
                            NULL as user_id,
                            MIN(COALESCE(
                                (e.cmetadata->>'created_at')::timestamp,
                                (e.cmetadata->>'created_date')::timestamp,
                                (e.cmetadata->>'upload_date')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as created_at,
                            MAX(COALESCE(
                                (e.cmetadata->>'updated_at')::timestamp,
                                (e.cmetadata->>'modified_date')::timestamp,
                                (e.cmetadata->>'created_at')::timestamp,
                                CURRENT_TIMESTAMP
                            )) as updated_at,
                            CASE WHEN COUNT(CASE WHEN e.embedding IS NOT NULL THEN 1 END) > 0 THEN true ELSE false END as has_embedding
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE {where_clause}
                        GROUP BY (e.cmetadata->>'filename'), c.name
                    """
                
                # Order by
                valid_order_by = ["created_at", "updated_at"]
                if order_by not in valid_order_by:
                    order_by = "created_at"
                
                valid_direction = ["asc", "desc"]
                if order_direction not in valid_direction:
                    order_direction = "desc"
                
                query += f" ORDER BY {order_by} {order_direction}"
                
                # Limit and offset
                query += " LIMIT :limit OFFSET :offset"
                params["limit"] = limit or 100
                params["offset"] = offset or 0
                
                # Get total count (count unique documents by filename)
                count_query = f"""
                    SELECT COUNT(DISTINCT (e.cmetadata->>'filename'))
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE {where_clause}
                """
                # count_params uses the same params as the main query (already includes user_id if needed)
                
                # Execute queries
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                
                count_result = await session.execute(text(count_query), params)
                total_count = count_result.scalar() or 0
                
                documents = []
                seen_files = set()  # Track unique files to avoid duplicates
                for row in rows:
                    metadata = row.metadata if isinstance(row.metadata, dict) else (json.loads(row.metadata) if row.metadata else {})
                    
                    # 방법4: 파일명 추출 개선 (Unknown이면 UUID 기반으로 변경)
                    filename = (
                        metadata.get("filename") or 
                        metadata.get("file_name") or 
                        metadata.get("source") or 
                        f"doc_{str(row.id)[:8]}"
                    )
                    
                    # 파일명이 "Unknown"이면 UUID 기반으로 변경
                    if filename == "Unknown":
                        filename = f"doc_{str(row.id)[:8]}"
                    
                    # Create unique key for file
                    file_key = f"{filename}_{row.collection_name}"
                    
                    # Only add if we haven't seen this file yet (to avoid duplicate chunks)
                    if file_key not in seen_files:
                        seen_files.add(file_key)
                        documents.append({
                            "id": str(row.id),
                            "content": (row.content[:200] + "..." if len(row.content) > 200 else row.content) if row.content else "",
                            "metadata": {**metadata, "filename": filename},
                            "collection_name": row.collection_name,
                            "user_id": str(row.user_id) if row.user_id else None,
                            "created_at": row.created_at.isoformat() if row.created_at else None,
                            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                            "embedding": row.has_embedding
                        })
                
                # Update total count to reflect unique files
                total_count = len(documents)
                
                return {
                    "success": True,
                    "documents": documents,
                    "total": total_count,
                    "limit": limit or 100,
                    "offset": offset or 0
                }
            else:
                # Original query for documents table
                if has_user_id:
                    query = """
                        SELECT
                            id,
                            content,
                            metadata,
                            collection_name,
                            user_id,
                            created_at,
                            updated_at,
                            CASE WHEN embedding IS NOT NULL THEN true ELSE false END as has_embedding
                        FROM documents
                        WHERE 1=1
                    """
                else:
                    query = """
                        SELECT
                            id,
                            content,
                            metadata,
                            collection_name,
                            NULL as user_id,
                            created_at,
                            updated_at,
                            CASE WHEN embedding IS NOT NULL THEN true ELSE false END as has_embedding
                        FROM documents
                        WHERE 1=1
                    """
                params = {}
                
                # Filter by collection
                if collection_name:
                    query += " AND collection_name = :collection_name"
                    params["collection_name"] = collection_name
                
                # Filter by user (if authenticated, show only user's documents)
                # For backward compatibility, if not authenticated, show all documents
                if user_id:
                    query += " AND (user_id = :user_id OR user_id IS NULL)"
                    params["user_id"] = user_id
                
                # Order by
                valid_order_by = ["created_at", "updated_at"]
                if order_by not in valid_order_by:
                    order_by = "created_at"
                
                valid_direction = ["asc", "desc"]
                if order_direction not in valid_direction:
                    order_direction = "desc"
                
                query += f" ORDER BY {order_by} {order_direction}"
                
                # Limit and offset
                query += " LIMIT :limit OFFSET :offset"
                params["limit"] = limit or 100
                params["offset"] = offset or 0
                
                # Get total count
                count_query = """
                    SELECT COUNT(*) 
                    FROM documents
                    WHERE 1=1
                """
                count_params = {}
                if collection_name:
                    count_query += " AND collection_name = :collection_name"
                    count_params["collection_name"] = collection_name
                if user_id:
                    count_query += " AND (user_id = :user_id OR user_id IS NULL)"
                    count_params["user_id"] = user_id
                
                # Get documents
                result = await session.execute(text(query), params)
                rows = result.fetchall()
                
                # Get total count
                count_result = await session.execute(text(count_query), count_params)
                total_count = count_result.scalar()
                
                documents = []
                for row in rows:
                    metadata = row.metadata if isinstance(row.metadata, dict) else (json.loads(row.metadata) if row.metadata else {})
                    documents.append({
                        "id": str(row.id),
                        "content": row.content[:200] + "..." if len(row.content) > 200 else row.content,  # Preview only
                        "metadata": metadata,
                        "collection_name": row.collection_name,
                        "user_id": str(row.user_id) if row.user_id else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                        "embedding": row.has_embedding
                    })
                
                return {
                    "success": True,
                    "documents": documents,
                    "total": total_count,
                    "limit": limit or 100,
                    "offset": offset or 0
                }
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/count")
async def get_document_count():
    """Get total document count"""
    try:
        count = await vector_service.get_document_count()
        return {"success": True, "count": count}
    except Exception as e:
        logger.error(f"Failed to get document count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoints
@app.post("/api/search")
async def search(request: SearchRequest):
    """Perform search using Google Custom Search API"""
    try:
        if request.deep_search:
            results = await search_service.deep_search(request.query, request.max_results)
        else:
            search_results = await search_service.search(request.query, request.max_results)
            results = {
                "enabled": True,
                "results": search_results,
                "metadata": {
                    "query": request.query,
                    "total_results": len(search_results)
                }
            }
        
        return {"success": True, "search_results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Vector search endpoints
@app.get("/api/vector/search")
async def vector_search(query: str, top_k: Optional[int] = None, similarity_threshold: Optional[float] = None):
    """Search for similar documents using optimized vector similarity with caching"""
    try:
        results = await vector_service.search_similar_optimized(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File upload endpoint with collection support
@app.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...), 
    collection_name: str = Form("documents"),
    create_embedding: str = Form("true")
):
    """Upload and process file"""
    extraction_result = None
    content = None
    should_create_embedding = False
    user_id = None
    
    # Try to get current user if authentication token is provided (optional for backward compatibility)
    try:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
            user = await auth_service.get_current_user(token)
            if user and hasattr(user, 'id'):
                user_id = user.id
    except:
        # If authentication fails, continue without user_id (backward compatibility)
        pass
    
    try:
        should_create_embedding = create_embedding.lower() == "true"
        logger.info(f"Starting file upload: {file.filename} to collection: {collection_name}, create_embedding: {should_create_embedding}, user_id: {user_id}")
        
        # Read file content
        content = await file.read()
        logger.info(f"File read successfully: {len(content)} bytes")
        
        # Extract text from file using file processing service
        logger.info("Starting text extraction...")
        extraction_result = FileProcessingService.extract_text_from_file(
            content, file.filename, file.content_type
        )
        logger.info(f"Text extraction completed: {len(extraction_result['text'])} characters")
        
        if not extraction_result["text"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to extract text from {file.filename}: {extraction_result['metadata'].get('error', 'Unknown error')}"
            )
        
        # Add to knowledge base with collection name
        if should_create_embedding:
            logger.info(f"Adding document to knowledge base in collection: {collection_name}")
            try:
                doc_id = await rag_service.add_document(
                    extraction_result["text"],
                    extraction_result["metadata"],
                    collection_name,
                    user_id
                )
                logger.info(f"Document added successfully with ID: {doc_id}")
                
                # Verify that embedding was actually created by checking the database
                actual_embedding_created = False
                try:
                    async with db_service.get_session() as session:
                        result = await session.execute(text("""
                            SELECT CASE WHEN embedding IS NOT NULL THEN true ELSE false END as has_embedding
                            FROM documents 
                            WHERE id = :doc_id
                        """), {"doc_id": doc_id})
                        row = result.fetchone()
                        if row:
                            actual_embedding_created = row.has_embedding
                        else:
                            # If document not found, check if it's a chunk ID (multiple chunks)
                            # For chunked documents, check if any chunk has embedding
                            result = await session.execute(text("""
                                SELECT COUNT(*) as count
                                FROM documents 
                                WHERE metadata::text LIKE :doc_id_pattern
                                AND embedding IS NOT NULL
                            """), {"doc_id_pattern": f"%{doc_id}%"})
                            chunk_count = result.scalar()
                            actual_embedding_created = chunk_count > 0
                except Exception as check_error:
                    logger.warning(f"Failed to verify embedding creation: {check_error}")
                    # Assume embedding was created if no error occurred during add_document
                    actual_embedding_created = True
                
                return {
                    "success": True,
                    "document_id": doc_id,
                    "filename": file.filename,
                    "size": len(content),
                    "extracted_text_length": len(extraction_result["text"]),
                    "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
                    "collection": collection_name,
                    "embedding_created": actual_embedding_created,
                    "message": f"File uploaded and processed successfully{' with embedding' if actual_embedding_created else ' without embedding'}"
                }
            except Exception as embed_error:
                # If embedding fails, save document without embedding as fallback
                error_msg = str(embed_error)
                # Also check the cause/context of the error
                error_cause = str(embed_error.__cause__) if embed_error.__cause__ else ""
                full_error_msg = f"{error_msg} {error_cause}".lower()
                logger.warning(f"Embedding generation failed, saving document without embedding: {error_msg}")
                
                # Check if it's really an embedding error (including "server error" patterns)
                # More comprehensive pattern matching
                is_embedding_error = (
                    "embedding" in full_error_msg or 
                    "ollama" in full_error_msg or 
                    "server error" in full_error_msg or
                    "500" in error_msg or
                    "internal server error" in full_error_msg or
                    "11434" in error_msg or  # Ollama port
                    "/api/embeddings" in error_msg.lower() or  # Embeddings endpoint
                    "nomic-embed" in full_error_msg or  # Embedding model name
                    "embeddings" in full_error_msg  # Plural form
                )
                
                if not is_embedding_error:
                    # Not an embedding error, re-raise
                    logger.error(f"Non-embedding error during document addition: {error_msg}")
                    raise
                
                # Save document without embedding
                try:
                    async with db_service.get_session() as session:
                        import uuid
                        doc_id = str(uuid.uuid4())

                        # Check if user_id column exists
                        try:
                            user_id_column_check = await session.execute(text("""
                                SELECT column_name
                                FROM information_schema.columns
                                WHERE table_name = 'documents' AND column_name = 'user_id'
                            """))
                            has_user_id = user_id_column_check.fetchone() is not None
                        except:
                            has_user_id = False

                        if has_user_id:
                            await session.execute(text("""
                                INSERT INTO documents (id, content, metadata, collection_name, embedding, user_id)
                                VALUES (:id, :content, :metadata, :collection_name, NULL, :user_id)
                            """), {
                                "id": doc_id,
                                "content": extraction_result["text"],
                                "metadata": json.dumps(extraction_result["metadata"]),
                                "collection_name": collection_name,
                                "user_id": user_id
                            })
                        else:
                            await session.execute(text("""
                                INSERT INTO documents (id, content, metadata, collection_name, embedding)
                                VALUES (:id, :content, :metadata, :collection_name, NULL)
                            """), {
                                "id": doc_id,
                                "content": extraction_result["text"],
                                "metadata": json.dumps(extraction_result["metadata"]),
                                "collection_name": collection_name
                            })
                        await session.commit()
                    
                    logger.info(f"Document saved without embedding with ID: {doc_id}")
                    return {
                        "success": True,
                        "document_id": doc_id,
                        "filename": file.filename,
                        "size": len(content),
                        "extracted_text_length": len(extraction_result["text"]),
                        "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
                        "collection": collection_name,
                        "embedding_created": False,
                        "warning": f"임베딩 생성 실패로 문서만 저장되었습니다. RAG 검색에는 사용할 수 없습니다. 오류: {error_msg}"
                    }
                except Exception as save_error:
                    # If saving without embedding also fails, raise original error
                    logger.error(f"Failed to save document without embedding: {save_error}")
                    if "ollama" in error_msg.lower() or "embedding" in error_msg.lower():
                        raise HTTPException(
                            status_code=500,
                            detail=f"임베딩 생성 실패: {error_msg}. Ollama 서버가 실행 중이고 '{settings.OLLAMA_EMBEDDING_MODEL}' 모델이 설치되어 있는지 확인하세요. 또는 벡터화 옵션을 끄고 문서만 저장할 수 있습니다."
                        )
                    raise
        else:
            # Just save the document without embedding
            logger.info(f"Saving document without embedding to collection: {collection_name}")
            async with db_service.get_session() as session:
                import uuid
                doc_id = str(uuid.uuid4())

                # Check if user_id column exists
                try:
                    user_id_column_check = await session.execute(text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = 'documents' AND column_name = 'user_id'
                    """))
                    has_user_id = user_id_column_check.fetchone() is not None
                except:
                    has_user_id = False

                if has_user_id:
                    await session.execute(text("""
                        INSERT INTO documents (id, content, metadata, collection_name, embedding, user_id)
                        VALUES (:id, :content, :metadata, :collection_name, NULL, :user_id)
                    """), {
                        "id": doc_id,
                        "content": extraction_result["text"],
                        "metadata": json.dumps(extraction_result["metadata"]),
                        "collection_name": collection_name,
                        "user_id": user_id
                    })
                else:
                    await session.execute(text("""
                        INSERT INTO documents (id, content, metadata, collection_name, embedding)
                        VALUES (:id, :content, :metadata, :collection_name, NULL)
                    """), {
                        "id": doc_id,
                        "content": extraction_result["text"],
                        "metadata": json.dumps(extraction_result["metadata"]),
                        "collection_name": collection_name
                    })
                await session.commit()
            logger.info(f"Document saved without embedding with ID: {doc_id}")
            
            # Verify that embedding was NOT created (since we explicitly set it to NULL)
            actual_embedding_created = False
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "extracted_text_length": len(extraction_result["text"]),
            "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
            "collection": collection_name,
            "embedding_created": actual_embedding_created,
            "message": f"File uploaded and processed successfully{' with embedding' if actual_embedding_created else ' without embedding'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"File upload failed: {e}", exc_info=True)
        
        # Check if it's an embedding error that should trigger fallback
        # Only try fallback if we have extraction_result (text extraction succeeded)
        # Check for various error patterns: embedding, ollama, server error, 500, etc.
        error_cause = str(e.__cause__) if e.__cause__ else ""
        full_error_msg = f"{error_msg} {error_cause}".lower()
        is_embedding_error = (
            "embedding" in full_error_msg or 
            "ollama" in full_error_msg or 
            "server error" in full_error_msg or
            "500" in error_msg or
            "internal server error" in full_error_msg or
            "11434" in error_msg or  # Ollama port
            "/api/embeddings" in error_msg.lower() or  # Embeddings endpoint
            "nomic-embed" in full_error_msg or  # Embedding model name
            "embeddings" in full_error_msg  # Plural form
        )
        
        if (should_create_embedding and 
            is_embedding_error and
            extraction_result is not None and extraction_result):
            # Try to save without embedding as final fallback
            try:
                logger.warning(f"Final fallback: saving document without embedding due to: {error_msg}")
                async with db_service.get_session() as session:
                    import uuid
                    doc_id = str(uuid.uuid4())
                    await session.execute(text("""
                        INSERT INTO documents (id, content, metadata, collection_name, embedding, user_id)
                        VALUES (:id, :content, :metadata, :collection_name, NULL, :user_id)
                    """), {
                        "id": doc_id,
                        "content": extraction_result["text"],
                        "metadata": json.dumps(extraction_result["metadata"]),
                        "collection_name": collection_name,
                        "user_id": user_id
                    })
                    await session.commit()
                
                logger.info(f"Document saved without embedding (final fallback) with ID: {doc_id}")
                return {
                    "success": True,
                    "document_id": doc_id,
                    "filename": file.filename,
                    "size": len(content),
                    "extracted_text_length": len(extraction_result["text"]),
                    "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
                    "collection": collection_name,
                    "embedding_created": False,
                    "warning": f"임베딩 생성 실패로 문서만 저장되었습니다. RAG 검색에는 사용할 수 없습니다. 오류: {error_msg}"
                }
            except Exception as final_error:
                logger.error(f"Final fallback also failed: {final_error}")
                # If even the final fallback fails, return error
                error_detail = f"파일 업로드 중 오류가 발생했습니다: {error_msg}. 문서 저장도 실패했습니다: {str(final_error)}"
                raise HTTPException(status_code=500, detail=error_detail)
        else:
            # Provide more detailed error information
            error_detail = f"파일 업로드 중 오류가 발생했습니다: {error_msg}"
            if "timeout" in error_msg.lower():
                error_detail += " (타임아웃 발생 - 파일이 너무 크거나 처리 시간이 오래 걸립니다)"
            elif "connection" in error_msg.lower():
                error_detail += " (연결 오류 - 서버 상태를 확인해주세요)"
            elif "embedding" in error_msg.lower() or "ollama" in error_msg.lower():
                error_detail += " (임베딩 생성 실패 - Ollama 서버 상태를 확인하거나 벡터화 옵션을 끄고 다시 시도해보세요)"
            raise HTTPException(status_code=500, detail=error_detail)

# LangChain file upload endpoint with collection support
@app.post("/api/langchain/upload")
async def upload_file_langchain(file: UploadFile = File(...), collection_name: str = Form("langchain_documents"), current_user: User = Depends(auth_controller.get_current_user)):
    """Upload and process file using LangChain"""
    try:
        # Log the received collection_name parameter for debugging
        logger.info(f"Received collection_name parameter: '{collection_name}' (type: {type(collection_name)})")
        
        # Ensure collection_name is not empty, None, or "undefined" - use default if needed
        if not collection_name or collection_name.strip() == "" or collection_name.strip().lower() == "undefined":
            collection_name = "langchain_documents"
            logger.warning(f"collection_name was empty, None, or 'undefined', using default: {collection_name}")
        
        logger.info(f"Starting LangChain file upload: {file.filename} to collection: {collection_name}")
        
        # Read file content
        content = await file.read()
        logger.info(f"File read successfully: {len(content)} bytes")
        
        # Extract text from file using file processing service
        logger.info("Starting text extraction...")
        extraction_result = FileProcessingService.extract_text_from_file(
            content, file.filename, file.content_type
        )
        logger.info(f"Text extraction completed: {len(extraction_result['text'])} characters")
        
        if not extraction_result["text"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to extract text from {file.filename}: {extraction_result['metadata'].get('error', 'Unknown error')}"
            )
        
        # Check collection ownership for non-default collections
        if collection_name != "langchain_documents":
            logger.info(f"Checking ownership for collection: {collection_name}")
            is_owner = await langchain_rag_service.check_collection_ownership(collection_name, current_user.id)
            if not is_owner:
                raise HTTPException(
                    status_code=403, 
                    detail=f"You don't have permission to upload files to collection '{collection_name}'. Only the collection owner can upload files."
                )
        
        # Always switch to the specified collection before adding document (ensures document goes to correct collection)
        logger.info(f"Switching to collection: {collection_name}")
        collection_set = await langchain_rag_service.set_collection(collection_name, current_user.id)
        
        # 컬렉션 설정 실패 시 오류 반환 (문서가 잘못된 컬렉션에 저장되는 것 방지)
        if not collection_set:
            logger.error(f"Failed to set collection '{collection_name}' for user {current_user.id}")
            raise HTTPException(
                status_code=400,
                detail=f"컬렉션 '{collection_name}' 설정에 실패했습니다. 컬렉션이 존재하지 않거나 접근 권한이 없습니다."
            )
        
        # Add to LangChain knowledge base
        # 방법2: 메타데이터에 filename 명시적으로 추가
        extraction_result["metadata"]["filename"] = file.filename
        extraction_result["metadata"]["file_name"] = file.filename  # 백업용
        logger.info(f"Adding document to LangChain knowledge base with filename: {file.filename}...")
        # collection_name을 명시적으로 전달하여 올바른 컬렉션에 저장되도록 보장
        doc_ids = await langchain_rag_service.add_document(
            extraction_result["text"],
            extraction_result["metadata"],
            collection_name  # 컬렉션 이름 명시적으로 전달
        )
        logger.info(f"Document added successfully with IDs: {doc_ids}")
        
        # DB 커밋이 완료될 때까지 잠시 대기 (방법3: 대기 시간 증가)
        await asyncio.sleep(1.0)  # 1초 대기하여 DB 트랜잭션 커밋 완료 보장
        
        return {
            "success": True,
            "document_ids": doc_ids,
            "filename": file.filename,
            "size": len(content),
            "extracted_text_length": len(extraction_result["text"]),
            "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
            "collection": collection_name,
            "message": "File uploaded and processed successfully with LangChain"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LangChain file upload failed: {e}")
        # Provide more detailed error information
        error_detail = f"LangChain 파일 업로드 중 오류가 발생했습니다: {str(e)}"
        if "timeout" in str(e).lower():
            error_detail += " (타임아웃 발생 - 파일이 너무 크거나 처리 시간이 오래 걸립니다)"
        elif "connection" in str(e).lower():
            error_detail += " (연결 오류 - 서버 상태를 확인해주세요)"
        raise HTTPException(status_code=500, detail=error_detail)

# Multiple files upload endpoint with collection support
@app.post("/api/upload/multiple")
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...), 
    collection_name: str = Form("documents")
):
    """Upload and process multiple files"""
    try:
        # Get current user if authenticated (optional for backward compatibility)
        user_id = None
        try:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization[7:]
                user = await auth_service.get_current_user(token)
                if user and hasattr(user, 'id'):
                    user_id = user.id
        except:
            pass
        
        # Switch to specified collection if different from current
        if collection_name != "langchain_documents":
            await langchain_rag_service.set_collection(collection_name)
        
        results = []
        
        for file in files:
            try:
                # Read file content
                content = await file.read()
                
                # Extract text from file
                extraction_result = FileProcessingService.extract_text_from_file(
                    content, file.filename, file.content_type
                )
                
                if not extraction_result["text"]:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"Failed to extract text: {extraction_result['metadata'].get('error', 'Unknown error')}"
                    })
                    continue
                
                # Add to knowledge base with collection name
                doc_id = await rag_service.add_document(
                    extraction_result["text"],
                    extraction_result["metadata"],
                    collection_name,
                    user_id
                )
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "document_id": doc_id,
                    "size": len(content),
                    "extracted_text_length": len(extraction_result["text"]),
                    "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown")
                })
                
            except Exception as e:
                logger.error(f"Failed to process file {file.filename}: {e}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        # Count successful uploads
        successful_uploads = sum(1 for r in results if r["success"])
        
        # DB 커밋이 완료될 때까지 잠시 대기 (방법3: 대기 시간 증가)
        if successful_uploads > 0:
            await asyncio.sleep(1.0)  # 1초 대기하여 DB 트랜잭션 커밋 완료 보장
        
        return {
            "success": True,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": len(files) - successful_uploads,
            "results": results,
            "collection": collection_name,
            "message": f"Processed {len(files)} files: {successful_uploads} successful, {len(files) - successful_uploads} failed"
        }
        
    except Exception as e:
        logger.error(f"Multiple file upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# LangChain multiple files upload endpoint with collection support
@app.post("/api/langchain/upload/multiple")
async def upload_multiple_files_langchain(files: List[UploadFile] = File(...), collection_name: str = Form("documents"), current_user: User = Depends(auth_controller.get_current_user)):
    """Upload and process multiple files using LangChain"""
    try:
        # Check collection ownership for non-default collections
        if collection_name != "langchain_documents":
            logger.info(f"Checking ownership for collection: {collection_name}")
            is_owner = await langchain_rag_service.check_collection_ownership(collection_name, current_user.id)
            if not is_owner:
                raise HTTPException(
                    status_code=403, 
                    detail=f"You don't have permission to upload files to collection '{collection_name}'. Only the collection owner can upload files."
                )
        
        # Always switch to the specified collection before adding documents
        logger.info(f"Switching to collection: {collection_name}")
        collection_set = await langchain_rag_service.set_collection(collection_name, current_user.id)
        
        # 컬렉션 설정 실패 시 오류 반환 (문서가 잘못된 컬렉션에 저장되는 것 방지)
        if not collection_set:
            logger.error(f"Failed to set collection '{collection_name}' for user {current_user.id}")
            raise HTTPException(
                status_code=400,
                detail=f"컬렉션 '{collection_name}' 설정에 실패했습니다. 컬렉션이 존재하지 않거나 접근 권한이 없습니다."
            )
        
        results = []
        
        for file in files:
            try:
                # Read file content
                content = await file.read()
                
                # Extract text from file
                extraction_result = FileProcessingService.extract_text_from_file(
                    content, file.filename, file.content_type
                )
                
                if not extraction_result["text"]:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"Failed to extract text: {extraction_result['metadata'].get('error', 'Unknown error')}"
                    })
                    continue
                
                # Add to LangChain knowledge base
                # 방법2: 메타데이터에 filename 명시적으로 추가
                extraction_result["metadata"]["filename"] = file.filename
                extraction_result["metadata"]["file_name"] = file.filename  # 백업용
                # collection_name을 명시적으로 전달하여 올바른 컬렉션에 저장되도록 보장
                doc_ids = await langchain_rag_service.add_document(
                    extraction_result["text"],
                    extraction_result["metadata"],
                    collection_name  # 컬렉션 이름 명시적으로 전달
                )
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "document_ids": doc_ids,
                    "size": len(content),
                    "extracted_text_length": len(extraction_result["text"]),
                    "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown")
                })
                
            except Exception as e:
                logger.error(f"Failed to process file {file.filename}: {e}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        # Count successful uploads
        successful_uploads = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": len(files) - successful_uploads,
            "results": results,
            "collection": collection_name,
            "message": f"Processed {len(files)} files with LangChain: {successful_uploads} successful, {len(files) - successful_uploads} failed"
        }
        
    except Exception as e:
        logger.error(f"LangChain multiple file upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Vector DB Collection Management endpoints
@app.get("/api/collections")
async def get_collections(current_user: User = Depends(auth_controller.get_current_user)):
    """Get list of available vector database collections for the current user"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Get LangChain RAG collections for the current user
        langchain_collections = await langchain_rag_service.get_collections(current_user.id)
        
        # Get basic RAG collections (documents table) - shared for all users
        basic_collections = await rag_service.get_available_collections()
        
        # Combine all collections
        all_collections = []
        
        # Add basic RAG collections first (shared)
        for collection in basic_collections:
            all_collections.append({
                "id": collection.get("id", "basic_rag"),
                "name": collection.get("name", "Unknown"),
                "metadata": collection.get("metadata", {}),
                "created_at": collection.get("created_at"),
                "document_count": collection.get("document_count", 0),
                "user_id": None  # Shared collection
            })
        
        # Add LangChain RAG collections (user-specific)
        for collection in langchain_collections:
            # Skip if already exists in basic collections
            if not any(c["name"] == collection.get("name") for c in all_collections):
                all_collections.append({
                    "id": collection.get("id", "langchain_rag"),
                    "name": collection.get("name", "Unknown"),
                    "metadata": collection.get("metadata", {}),
                    "created_at": collection.get("created_at"),
                    "document_count": collection.get("document_count", 0),
                    "user_id": collection.get("user_id"),
                    "type": collection.get("type", "personal" if collection.get("user_id") else "shared"),
                    "is_shared": collection.get("is_shared", False)
                })
        
        logger.info(f"Returning {len(all_collections)} collections")
        for c in all_collections:
            logger.info(f"Collection: {c['name']} ({c['id']}) - Count: {c['document_count']}")
        
        current_collection = getattr(langchain_rag_service, 'current_collection', 'langchain_documents')
        
        return {
            "success": True,
            "collections": all_collections,
            "current_collection": current_collection,
            "total_collections": len(all_collections)
        }
        
    except Exception as e:
        logger.error(f"Failed to get collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/collections/active")
async def get_current_collection():
    """Get the currently active collection"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        current_collection = getattr(langchain_rag_service, 'current_collection', 'documents')
        
        return {
            "success": True,
            "current_collection": current_collection
        }
        
    except Exception as e:
        logger.error(f"Failed to get current collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collections/switch")
async def switch_collection(request: CollectionRequest, current_user: User = Depends(auth_controller.get_current_user)):
    """Switch the active collection for RAG queries"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        success = await langchain_rag_service.set_collection(request.collection_name, current_user.id)
        
        if success:
            return {
                "success": True,
                "message": f"Switched to collection: {request.collection_name}",
                "current_collection": request.collection_name
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to switch to collection: {request.collection_name}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collections/info/{collection_name}")
async def get_collection_info(collection_name: str):
    """Get detailed information about a specific collection"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Try to get collection info from basic RAG (documents table) first
        try:
            basic_collection_info = await vector_service.get_collection(collection_name)
            if basic_collection_info and basic_collection_info.get("document_count", 0) >= 0:
                # Found in basic RAG collections
                return {
                    "success": True,
                    "collection": {
                        "name": basic_collection_info.get("name", collection_name),
                        "document_count": basic_collection_info.get("document_count", 0),
                        "created_at": basic_collection_info.get("created_at"),
                        "updated_at": basic_collection_info.get("updated_at"),
                        "type": "basic_rag"
                    }
                }
        except Exception as basic_error:
            logger.debug(f"Collection not found in basic RAG: {basic_error}")
        
        # Try LangChain RAG collections
        try:
            langchain_collection_info = await langchain_rag_service.get_collection_info(collection_name)
            if langchain_collection_info:
                return {
                    "success": True,
                    "collection": {
                        **langchain_collection_info,
                        "type": "langchain_rag"
                    }
                }
        except Exception as langchain_error:
            logger.debug(f"Collection not found in LangChain RAG: {langchain_error}")
        
        # If not found in either, return empty collection info (collection exists but has no documents)
        return {
            "success": True,
            "collection": {
                "name": collection_name,
                "document_count": 0,
                "created_at": None,
                "updated_at": None,
                "type": "unknown"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collections/create")
async def create_collection(request: CreateCollectionRequest, current_user: User = Depends(auth_controller.get_current_user)):
    """Create a new collection (personal or shared) for the current user"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Validate type
        if request.type not in ["personal", "shared"]:
            raise HTTPException(status_code=400, detail="Type must be 'personal' or 'shared'")
        
        is_shared = request.type == "shared"
        
        result = await langchain_rag_service.create_collection(
            request.collection_name, 
            request.description,
            current_user.id,
            is_shared=is_shared
        )
        
        collection_type = "공유" if is_shared else "개인"
        return {
            "success": True,
            "message": f"{collection_type} 데이터셋 '{request.collection_name}'이(가) 생성되었습니다",
            "collection": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collections/create-shared")
async def create_shared_collection(request: CreateCollectionRequest, current_user: User = Depends(auth_controller.get_current_user)):
    """Create a new shared collection accessible by all users"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Create shared collection (user_id = current_user.id for ownership tracking)
        result = await langchain_rag_service.create_collection(
            request.collection_name, 
            request.description,
            current_user.id,  # Store creator's user_id for ownership tracking
            is_shared=True    # Mark as shared collection
        )
        
        return {
            "success": True,
            "message": f"Shared collection '{request.collection_name}' created successfully",
            "collection": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create shared collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/collections/{collection_name}/change-type")
async def change_collection_type(collection_name: str, request: dict, current_user: User = Depends(auth_controller.get_current_user)):
    """Change collection type between personal and shared"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        new_type = request.get("type")  # "personal" or "shared"
        if new_type not in ["personal", "shared"]:
            raise HTTPException(status_code=400, detail="Type must be 'personal' or 'shared'")
        
        # Get current collection info
        collections = await langchain_rag_service.get_collections(current_user.id)
        current_collection = None
        for collection in collections:
            if collection.get("name") == collection_name:
                current_collection = collection
                break
        
        if not current_collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Check if user owns the collection
        current_user_id = current_collection.get("user_id")
        if current_user_id is not None and current_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to modify this collection")
        elif current_user_id is None:
            # Shared collections (user_id = NULL) - check created_by in metadata
            metadata = current_collection.get("metadata", {})
            created_by = metadata.get("created_by")
            if created_by != current_user.id:
                raise HTTPException(status_code=403, detail="You don't have permission to modify this collection")
        
        # Determine new user_id based on type
        # For personal collections: set user_id to current user
        # For shared collections: set user_id to None (but keep original creator info in metadata)
        if new_type == "personal":
            new_user_id = current_user.id
        else:  # shared
            new_user_id = None  # Shared collections have user_id = None
        
        # Update collection type
        result = await langchain_rag_service.change_collection_type(collection_name, new_user_id)
        
        type_text = "개인" if new_type == "personal" else "공유"
        return {
            "success": True,
            "message": f"Collection '{collection_name}' changed to {type_text} collection successfully",
            "collection": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to change collection type: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/collections/{collection_name}")
async def delete_collection(collection_name: str, current_user: User = Depends(auth_controller.get_current_user)):
    """Delete a collection and all its documents"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Prevent deletion of default collections
        if collection_name in ["documents", "langchain_documents"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete the default collection '{collection_name}'"
            )
        
        deleted_results = {}
        
        # Try to delete from Basic RAG (documents table) first
        try:
            basic_deleted = await vector_service.delete_collection(collection_name)
            if basic_deleted:
                deleted_results["basic_rag"] = True
                logger.info(f"Deleted Basic RAG collection '{collection_name}'")
        except Exception as basic_error:
            logger.debug(f"Collection '{collection_name}' not found in Basic RAG: {basic_error}")
            deleted_results["basic_rag"] = False
        
        # Try to delete from LangChain RAG
        try:
            langchain_result = await langchain_rag_service.delete_collection(collection_name, current_user.id)
            deleted_results["langchain_rag"] = langchain_result
            logger.info(f"Deleted LangChain RAG collection '{collection_name}'")
        except ValueError as langchain_error:
            # Collection doesn't exist in LangChain RAG - this is OK
            logger.debug(f"Collection '{collection_name}' not found in LangChain RAG: {langchain_error}")
            deleted_results["langchain_rag"] = False
        except Exception as langchain_error:
            # Other errors (like permission) - log but don't fail if Basic RAG deletion succeeded
            if "not authorized" in str(langchain_error).lower() or "permission" in str(langchain_error).lower():
                logger.warning(f"Not authorized to delete LangChain collection '{collection_name}': {langchain_error}")
                deleted_results["langchain_rag"] = False
            else:
                logger.debug(f"Collection '{collection_name}' not found in LangChain RAG: {langchain_error}")
                deleted_results["langchain_rag"] = False
        
        # Check if at least one deletion succeeded
        if deleted_results.get("basic_rag") or deleted_results.get("langchain_rag"):
            return {
                "success": True,
                "message": f"Collection '{collection_name}' deleted successfully",
                "deleted_from": {
                    "basic_rag": deleted_results.get("basic_rag", False),
                    "langchain_rag": deleted_results.get("langchain_rag", False)
                }
            }
        else:
            return {
                "success": False,
                "message": f"Collection '{collection_name}' does not exist",
                "error": "COLLECTION_NOT_FOUND"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/collections/rename")
async def rename_collection(request: RenameCollectionRequest, current_user: User = Depends(auth_controller.get_current_user)):
    """Rename a collection"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        result = await langchain_rag_service.rename_collection(
            request.old_name, 
            request.new_name,
            current_user.id
        )
        
        return {
            "success": True,
            "message": f"Collection renamed from '{request.old_name}' to '{request.new_name}'",
            "result": result
        }
        
    except ValueError as e:
        if "not authorized" in str(e).lower() or "permission" in str(e).lower():
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to rename collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Markdown export endpoints
@app.post("/api/chat/export/markdown")
async def export_chat_markdown(request: MarkdownExportRequest):
    """Export chat session to markdown format"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Get chat history for the session
        try:
            messages = await chat_service.get_chat_history(request.session_id)
            history_response = {
                "success": True,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "sources": [
                        {
                            "filename": s.filename, 
                            "similarity_score": s.similarity_score,
                            "content_preview": s.content_preview,
                            "document_id": s.document_id
                        } 
                        for s in msg.sources
                    ] if msg.sources else [],
                        "accuracy": {
                            "confidence_score": msg.accuracy.confidence_score,
                            "context_count": msg.accuracy.context_count,
                            "avg_similarity": msg.accuracy.avg_similarity,
                            "fallback_used": msg.accuracy.fallback_used
                        } if msg.accuracy else None,
                        "metadata": msg.metadata
                    }
                    for msg in messages
                ]
            }
        except Exception as e:
            history_response = {"success": False, "error": str(e)}
        
        if not history_response.get("success"):
            raise HTTPException(
                status_code=404, 
                detail=f"Session '{request.session_id}' not found or error loading history"
            )
        
        messages = history_response.get("messages", [])
        
        if not messages:
            raise HTTPException(
                status_code=400, 
                detail="No messages found in the session"
            )
        
        # Generate markdown content
        markdown_content = markdown_service.generate_chat_markdown(
            messages=messages,
            session_id=request.session_id,
            session_name=request.session_name,
            include_metadata=request.include_metadata
        )
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_export_{request.session_id}_{timestamp}.md"
        
        # Save to file
        filepath = markdown_service.save_markdown_to_file(markdown_content, filename)
        
        return {
            "success": True,
            "message": "Markdown export generated successfully",
            "filename": filename,
            "filepath": filepath,
            "content": markdown_content,
            "message_count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export chat markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/export/markdown/single")
async def export_single_message_markdown(request: SingleMessageMarkdownRequest):
    """Export a single message to markdown format"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Generate markdown content for single message
        markdown_content = markdown_service.generate_single_message_markdown(
            message=request.message,
            include_metadata=request.include_metadata
        )
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        role = request.message.get("role", "unknown")
        filename = f"message_{role}_{timestamp}.md"
        
        # Save to file
        filepath = markdown_service.save_markdown_to_file(markdown_content, filename)
        
        return {
            "success": True,
            "message": "Single message markdown export generated successfully",
            "filename": filename,
            "filepath": filepath,
            "content": markdown_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export single message markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/export/markdown/stats")
async def get_markdown_export_stats():
    """Get statistics about exported markdown files"""
    try:
        stats = markdown_service.get_export_stats()
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get markdown export stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/export/markdown/download/{filename}")
async def download_markdown_file(filename: str):
    """Download a specific markdown file"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Security check - ensure filename is safe
        if not filename.endswith('.md') or '..' in filename or '/' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        filepath = os.path.join(markdown_service.export_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "filename": filename,
            "content": content,
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download markdown file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Authentication endpoints
@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        logger.info(f"Register request for user: {request.username}")
        result = await auth_controller.register(request)
        logger.info(f"Register result: success={result.success}, message={result.message}")
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        # Convert AuthResponse to dictionary for JSON serialization
        response_dict = {
            "success": result.success,
            "message": result.message,
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "expires_in": result.expires_in
        }
        
        # Convert User object to dictionary
        if result.user:
            response_dict["user"] = {
                "id": result.user.id,
                "username": result.user.username,
                "email": result.user.email,
                "role": result.user.role.value,
                "is_active": result.user.is_active,
                "created_at": result.user.created_at.isoformat() if result.user.created_at else None,
                "updated_at": result.user.updated_at.isoformat() if result.user.updated_at else None,
                "last_login": result.user.last_login.isoformat() if result.user.last_login else None
            }
        
        return response_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e) if str(e) else "Registration failed")

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    try:
        logger.info(f"Login request for user: {request.username}")
        result = await auth_controller.login(request)
        logger.info(f"Login result: success={result.success}, message={result.message}")
        if not result.success:
            raise HTTPException(status_code=401, detail=result.message)
        
        # Convert AuthResponse to dictionary for JSON serialization
        response_dict = {
            "success": result.success,
            "message": result.message,
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "expires_in": result.expires_in
        }
        
        # Convert User object to dictionary
        if result.user:
            response_dict["user"] = {
                "id": result.user.id,
                "username": result.user.username,
                "email": result.user.email,
                "role": result.user.role.value,
                "is_active": result.user.is_active,
                "created_at": result.user.created_at.isoformat() if result.user.created_at else None,
                "updated_at": result.user.updated_at.isoformat() if result.user.updated_at else None,
                "last_login": result.user.last_login.isoformat() if result.user.last_login else None
            }
        
        return response_dict
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail=str(e) if str(e) else "Login failed")

@app.post("/api/auth/refresh")
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token"""
    try:
        result = auth_controller.refresh_token(request.refresh_token)
        if not result.success:
            raise HTTPException(status_code=401, detail=result.message)
        
        # Convert AuthResponse to dictionary for JSON serialization
        response_dict = {
            "success": result.success,
            "message": result.message,
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "expires_in": result.expires_in
        }
        
        # Convert User object to dictionary
        if result.user:
            response_dict["user"] = {
                "id": result.user.id,
                "username": result.user.username,
                "email": result.user.email,
                "role": result.user.role.value,
                "is_active": result.user.is_active,
                "created_at": result.user.created_at.isoformat() if result.user.created_at else None,
                "updated_at": result.user.updated_at.isoformat() if result.user.updated_at else None,
                "last_login": result.user.last_login.isoformat() if result.user.last_login else None
            }
        
        return response_dict
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me")
async def get_current_user(current_user = Depends(auth_controller.get_current_user)):
    """Get current user information"""
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
    }

@app.post("/api/auth/logout")
async def logout(current_user = Depends(auth_controller.get_current_user)):
    """Logout user"""
    try:
        success = auth_controller.logout(current_user.id)
        return {
            "success": success,
            "message": "로그아웃되었습니다." if success else "로그아웃 중 오류가 발생했습니다."
        }
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TokenVerifyRequest(BaseModel):
    token: str

@app.post("/api/auth/verify")
async def verify_token(request: TokenVerifyRequest):
    """Verify if token is valid"""
    try:
        is_valid = auth_controller.verify_token(request.token)
        return {
            "success": True,
            "valid": is_valid
        }
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return {
            "success": False,
            "valid": False,
            "error": str(e)
        }

# Accuracy measurement endpoints
@app.post("/api/accuracy/measure")
async def measure_query_accuracy(request: AccuracyQueryRequest):
    """Measure accuracy for a single query"""
    try:
        result = await accuracy_controller.measure_single_query(
            request.query, 
            request.expected_answer
        )
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Accuracy measurement failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accuracy/test-suite")
async def run_accuracy_test_suite(request: AccuracyTestSuiteRequest):
    """Run a comprehensive accuracy test suite"""
    try:
        result = await accuracy_controller.run_test_suite(request.test_queries)
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Accuracy test suite failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accuracy/system-health")
async def get_system_health():
    """Get system health metrics"""
    try:
        result = await accuracy_controller.get_system_health()
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accuracy/sample-queries")
async def get_sample_test_queries():
    """Get sample test queries for accuracy testing"""
    try:
        result = accuracy_controller.get_sample_test_queries()
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Failed to get sample queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Feedback endpoints
class FeedbackRequest(BaseModel):
    user_id: str
    session_id: str
    message_id: str
    feedback_type: str
    rating: Optional[int] = None
    is_positive: Optional[bool] = None
    comment: Optional[str] = None
    timestamp: Optional[str] = None

@app.post("/api/feedback/submit")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback"""
    try:
        from services.feedback_service import feedback_service, FeedbackType
        
        # Convert string to FeedbackType enum
        try:
            feedback_type = FeedbackType(request.feedback_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid feedback type: {request.feedback_type}")
        
        result = feedback_service.submit_feedback(
            user_id=request.user_id,
            session_id=request.session_id,
            message_id=request.message_id,
            feedback_type=feedback_type,
            rating=request.rating,
            is_positive=request.is_positive,
            comment=request.comment
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback/analytics")
async def get_feedback_analytics(user_id: Optional[str] = None, days: int = 30):
    """Get feedback analytics"""
    try:
        from services.feedback_service import feedback_service
        
        analytics = feedback_service.get_feedback_analytics(user_id=user_id, days=days)
        
        return {
            "success": True,
            "analytics": {
                "total_feedback": analytics.total_feedback,
                "positive_feedback": analytics.positive_feedback,
                "negative_feedback": analytics.negative_feedback,
                "average_rating": analytics.average_rating,
                "feedback_by_type": analytics.feedback_by_type,
                "recent_trends": analytics.recent_trends,
                "quality_issues": analytics.quality_issues,
                "improvement_suggestions": analytics.improvement_suggestions
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Model management endpoints
@app.get("/api/models/available")
async def get_available_models():
    """Get available models for selection"""
    try:
        models = await ollama_service.get_available_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/config/{model_type}")
async def get_model_config(model_type: str):
    """Get configuration for a specific model type"""
    try:
        config = await ollama_service.get_model_config(model_type)
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        logger.error(f"Failed to get model config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User management endpoints
@app.get("/api/users")
async def get_all_users(current_user = Depends(auth_controller.get_current_user)):
    """Get all users (admin only)"""
    try:
        # Check if user is admin (check by ID for now)
        logger.info(f"Current user ID: {current_user.id}")
        logger.info(f"Current user role: {current_user.role}")
        logger.info(f"Admin user ID: {settings.ADMIN_USER_ID}")
        logger.info(f"Permission check: {current_user.id == settings.ADMIN_USER_ID}")
        if current_user.id != settings.ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
        from backend.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        users = await user_repo.get_all_users()
        
        # Convert User objects to dictionaries
        user_list = []
        for user in users:
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            user_list.append(user_dict)
        
        return {
            "success": True,
            "users": user_list,
            "total": len(user_list)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}")
async def get_user(user_id: str, current_user = Depends(auth_controller.get_current_user)):
    """Get user by ID (admin only)"""
    try:
        # Check if user is admin (check by ID for now)
        if current_user.id != settings.ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
        from backend.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        user = await user_repo.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        return {
            "success": True,
            "user": user_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"
    is_active: bool = True

@app.post("/api/users")
async def create_user(request: UserCreateRequest, current_user = Depends(auth_controller.get_current_user)):
    """Create a new user (admin only)"""
    try:
        # Check if user is admin (check by ID for now)
        if current_user.id != settings.ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
        from backend.repositories.user_repository import UserRepository
        from backend.models.user import User, UserRole
        import uuid
        
        user_repo = UserRepository()
        
        # Check if username or email already exists
        existing_user_by_username = await user_repo.get_user_by_username(request.username)
        if existing_user_by_username:
            logger.warning(f"Username already exists: {request.username}")
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다.")
        
        existing_user_by_email = await user_repo.get_user_by_email(request.email)
        if existing_user_by_email:
            logger.warning(f"Email already exists: {request.email}")
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            username=request.username,
            email=request.email,
            password_hash=auth_service.hash_password(request.password),
            role=UserRole(request.role),
            is_active=request.is_active
        )
        
        # Save user
        logger.info(f"Creating user: {user.username}, {user.email}")
        if await user_repo.create_user(user):
            logger.info(f"User created successfully: {user.id}")
            return {
                "success": True,
                "message": "사용자가 성공적으로 생성되었습니다.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
            }
        else:
            logger.error(f"Failed to create user: {user.username}")
            raise HTTPException(status_code=500, detail="사용자 생성 중 오류가 발생했습니다.")
            
    except HTTPException as e:
        logger.error(f"HTTP Exception in create_user: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 생성 중 오류가 발생했습니다: {str(e)}")

class UserUpdateRequest(BaseModel):
    username: str
    email: str
    role: str
    is_active: bool

@app.put("/api/users/{user_id}")
async def update_user(user_id: str, request: UserUpdateRequest, current_user = Depends(auth_controller.get_current_user)):
    """Update user (admin only)"""
    try:
        # Check if user is admin (check by ID for now)
        if current_user.id != settings.ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
        from backend.repositories.user_repository import UserRepository
        from backend.models.user import User, UserRole
        
        user_repo = UserRepository()
        user = await user_repo.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # Check if username or email already exists (excluding current user)
        existing_user_by_username = await user_repo.get_user_by_username(request.username)
        if existing_user_by_username and existing_user_by_username.id != user_id:
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다.")
        
        existing_user_by_email = await user_repo.get_user_by_email(request.email)
        if existing_user_by_email and existing_user_by_email.id != user_id:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
        
        # Update user information
        user.username = request.username
        user.email = request.email
        user.role = UserRole(request.role)
        user.is_active = request.is_active
        user.updated_at = datetime.now()
        
        # Save updated user
        if await user_repo.update_user(user):
            return {
                "success": True,
                "message": "사용자 정보가 성공적으로 업데이트되었습니다.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
            }
        else:
            raise HTTPException(status_code=500, detail="사용자 정보 업데이트 중 오류가 발생했습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user = Depends(auth_controller.get_current_user)):
    """Delete user (admin only)"""
    try:
        # Check if user is admin (check by ID for now)
        if current_user.id != settings.ADMIN_USER_ID:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
        # Prevent admin from deleting themselves
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="자신의 계정을 삭제할 수 없습니다.")
        
        from backend.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        
        # Check if user exists
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # Delete user
        if await user_repo.delete_user(user_id):
            return {
                "success": True,
                "message": "사용자가 성공적으로 삭제되었습니다."
            }
        else:
            raise HTTPException(status_code=500, detail="사용자 삭제 중 오류가 발생했습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint
@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working", "status": "success"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL_APP.lower()
    )
