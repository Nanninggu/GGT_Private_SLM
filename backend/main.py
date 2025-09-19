"""
FastAPI backend server for the chatbot
Converted from Spring Boot with enhanced RAG capabilities
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
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

from controllers.chat_controller import ChatController
from controllers.auth_controller import auth_controller
from controllers.web_search_controller import router as web_search_router
from controllers.accuracy_controller import AccuracyController
from config.settings import settings
from services.database_service import db_service
from services.vector_service import vector_service
from services.ollama_service import ollama_service
from services.rag_service import rag_service
from services.search_service import search_service
from services.langchain_rag_service import langchain_rag_service
from services.prompt_service import prompt_service
from services.file_processing_service import FileProcessingService
from services.markdown_service import MarkdownService
from services.accuracy_service import accuracy_service

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

class CollectionRequest(BaseModel):
    collection_name: str

class CreateCollectionRequest(BaseModel):
    collection_name: str
    description: Optional[str] = ""

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
        await langchain_rag_service.initialize()
        await accuracy_service.initialize()
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
chat_controller = ChatController()
accuracy_controller = AccuracyController()
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
        result = auth_controller.login(request)
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
async def create_session():
    """Create a new chat session"""
    result = chat_controller.create_session()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/chat/message")
async def send_message(request: MessageRequest):
    """Send a message and get AI response using selected RAG mode"""
    session_id = request.session_id or "default"
    rag_mode = request.rag_mode or "LangChain RAG"
    
    try:
        # Use selected RAG mode
        logger.info(f"Processing {rag_mode} query: {request.message[:100]}...")
        
        if rag_mode == "기본 RAG":
            # Use basic RAG service
            result = await rag_service.rag_query(request.message, session_id)
        else:
            # Use LangChain RAG service (default)
            result = await langchain_rag_service.rag_query(request.message, session_id)
        
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
        
        # Format response for frontend
        return {
            "success": True,
            "user_message": {
                "id": str(uuid.uuid4()),
                "content": request.message,
                "timestamp": datetime.now().isoformat()
            },
            "assistant_message": {
                "id": str(uuid.uuid4()),
                "content": result["response"],
                "timestamp": datetime.now().isoformat()
            },
            "context": result.get("context", []),
            "metadata": result.get("metadata", {})
        }
        
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def stream_chat(request: ChatRequest):
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
                    result = await langchain_rag_service.rag_query(request.message, request.session_id)
                
                if result["success"] and result.get("response"):
                    # Stream the response
                    response_text = result["response"]
                    
                    # Send context information first
                    if result.get("context"):
                        context_info = {
                            "type": "context",
                            "sources": [doc.get("filename", "Unknown") for doc in result["context"]],
                            "context_files": result.get("metadata", {}).get("context_files", []),
                            "source_collection": result.get("metadata", {}).get("source_collection", "documents"),
                            "context_count": len(result["context"]),
                            "detailed_sources": result["context"],
                            "similarity_scores": [doc.get("similarity", 0) for doc in result["context"]]
                        }
                        yield {
                            "event": "context",
                            "data": json.dumps(context_info)
                        }
                    
                    # Stream the response text with improved chunking
                    chunk_size = 5  # Smaller chunks for smoother effect
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i+chunk_size]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.03)  # Slightly slower for better readability
                    
                    # Send completion signal
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True
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
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.03)
                    
                    # Send completion signal
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True
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
                    result = await langchain_rag_service.rag_query(request.message, request.session_id)
                
                if result["success"] and result.get("response"):
                    response_text = result["response"]
                    
                    # Send context information first
                    if result.get("context"):
                        context_info = {
                            "type": "context",
                            "sources": [doc.get("metadata", {}).get("filename", "Unknown") for doc in result["context"]],
                            "context_files": result.get("metadata", {}).get("context_files", []),
                            "similarity_scores": [doc.get("similarity", 0) for doc in result["context"]],
                            "context_count": len(result["context"])
                        }
                        yield {
                            "event": "context",
                            "data": json.dumps(context_info)
                        }
                    
                    # Stream the response text with improved chunking
                    chunk_size = 5  # Smaller chunks for smoother effect
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i+chunk_size]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.03)  # Slightly slower for better readability
                    
                    # Send completion signal
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True
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
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.03)
                    
                    # Send completion signal
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True
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
    result = chat_controller.get_chat_history(session_id, limit)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/chat/sessions")
async def get_sessions():
    """Get all session IDs"""
    result = chat_controller.get_sessions()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/api/chat/session/{session_id}/exists")
async def check_session_exists(session_id: str):
    """Check if a session exists without loading all sessions"""
    result = chat_controller.check_session_exists(session_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.delete("/api/chat/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session"""
    result = chat_controller.clear_session(session_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.delete("/api/chat/sessions/all")
async def clear_all_sessions():
    """Clear all sessions except default"""
    result = chat_controller.clear_all_sessions()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

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
            rag_result = await langchain_rag_service.rag_query(request.message, request.session_id)
        
        if rag_result["success"]:
            assistant_message = {
                "id": assistant_message_id,
                "content": rag_result["response"],
                "timestamp": datetime.now().isoformat()
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
    """Search for similar documents using vector similarity"""
    try:
        results = await vector_service.search_similar(
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
async def upload_file(file: UploadFile = File(...), collection_name: str = Form("documents")):
    """Upload and process file"""
    try:
        logger.info(f"Starting file upload: {file.filename} to collection: {collection_name}")
        
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
        logger.info(f"Adding document to knowledge base in collection: {collection_name}")
        doc_id = await rag_service.add_document(
            extraction_result["text"],
            extraction_result["metadata"],
            collection_name
        )
        logger.info(f"Document added successfully with ID: {doc_id}")
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "extracted_text_length": len(extraction_result["text"]),
            "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
            "collection": collection_name,
            "message": "File uploaded and processed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        # Provide more detailed error information
        error_detail = f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        if "timeout" in str(e).lower():
            error_detail += " (타임아웃 발생 - 파일이 너무 크거나 처리 시간이 오래 걸립니다)"
        elif "connection" in str(e).lower():
            error_detail += " (연결 오류 - 서버 상태를 확인해주세요)"
        raise HTTPException(status_code=500, detail=error_detail)

# LangChain file upload endpoint with collection support
@app.post("/api/langchain/upload")
async def upload_file_langchain(file: UploadFile = File(...), collection_name: str = Form("langchain_documents")):
    """Upload and process file using LangChain"""
    try:
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
        
        # Switch to specified collection if different from current
        if collection_name != "langchain_documents":
            logger.info(f"Switching to collection: {collection_name}")
            await langchain_rag_service.set_collection(collection_name)
        
        # Add to LangChain knowledge base
        logger.info("Adding document to LangChain knowledge base...")
        doc_ids = await langchain_rag_service.add_document(
            extraction_result["text"],
            extraction_result["metadata"]
        )
        logger.info(f"Document added successfully with IDs: {doc_ids}")
        
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
async def upload_multiple_files(files: List[UploadFile] = File(...), collection_name: str = Form("documents")):
    """Upload and process multiple files"""
    try:
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
                    collection_name
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
async def upload_multiple_files_langchain(files: List[UploadFile] = File(...), collection_name: str = Form("documents")):
    """Upload and process multiple files using LangChain"""
    try:
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
                
                # Add to LangChain knowledge base
                doc_ids = await langchain_rag_service.add_document(
                    extraction_result["text"],
                    extraction_result["metadata"]
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
async def get_collections():
    """Get list of available vector database collections"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        # Get LangChain RAG collections
        langchain_collections = await langchain_rag_service.get_available_collections()
        
        # Get basic RAG collections (documents table)
        basic_collections = await rag_service.get_available_collections()
        
        # Combine all collections
        all_collections = []
        
        # Add basic RAG collections first
        for collection in basic_collections:
            all_collections.append({
                "id": collection.get("id", "basic_rag"),
                "name": collection.get("name", "Unknown"),
                "metadata": collection.get("metadata", {}),
                "created_at": collection.get("created_at"),
                "document_count": collection.get("document_count", 0)
            })
        
        # Add LangChain RAG collections
        for collection in langchain_collections:
            # Skip if already exists in basic collections
            if not any(c["name"] == collection.get("name") for c in all_collections):
                all_collections.append({
                    "id": collection.get("id", "langchain_rag"),
                    "name": collection.get("name", "Unknown"),
                    "metadata": collection.get("metadata", {}),
                    "created_at": collection.get("created_at"),
                    "document_count": collection.get("document_count", 0)
                })
        
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
async def switch_collection(request: CollectionRequest):
    """Switch the active collection for RAG queries"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        success = await langchain_rag_service.set_collection(request.collection_name)
        
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
        
        collection_info = await langchain_rag_service.get_collection_info(collection_name)
        
        if not collection_info:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
        return {
            "success": True,
            "collection": collection_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/collections/create")
async def create_collection(request: CreateCollectionRequest):
    """Create a new collection"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        result = await langchain_rag_service.create_collection(
            request.collection_name, 
            request.description
        )
        
        return {
            "success": True,
            "message": f"Collection '{request.collection_name}' created successfully",
            "collection": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection and all its documents"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        result = await langchain_rag_service.delete_collection(collection_name)
        
        return {
            "success": True,
            "message": f"Collection '{collection_name}' deleted successfully",
            "result": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/collections/rename")
async def rename_collection(request: RenameCollectionRequest):
    """Rename a collection"""
    try:
        if not services_initialized:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        result = await langchain_rag_service.rename_collection(
            request.old_name, 
            request.new_name
        )
        
        return {
            "success": True,
            "message": f"Collection renamed from '{request.old_name}' to '{request.new_name}'",
            "result": result
        }
        
    except ValueError as e:
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
        history_response = chat_controller.get_chat_history(request.session_id)
        
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
        result = auth_controller.register(request)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    try:
        logger.info(f"Login request for user: {request.username}")
        result = auth_controller.login(request)
        logger.info(f"Login result: success={result.success}, message={result.message}")
        if not result.success:
            raise HTTPException(status_code=401, detail=result.message)
        return result
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/refresh")
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token"""
    try:
        result = auth_controller.refresh_token(request.refresh_token)
        if not result.success:
            raise HTTPException(status_code=401, detail=result.message)
        return result
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
        raise HTTPException(status_code=500, detail=str(e))

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
