"""
FastAPI backend server for the chatbot
Converted from Spring Boot with enhanced RAG capabilities
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
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
from config.settings import settings
from services.database_service import db_service
from services.vector_service import vector_service
from services.ollama_service import ollama_service
from services.rag_service import rag_service
from services.search_service import search_service
from services.langchain_rag_service import langchain_rag_service
from services.prompt_service import prompt_service
from services.file_processing_service import FileProcessingService

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

# Initialize controller
chat_controller = ChatController()

# Request models
class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_rag: bool = True
    use_search: bool = False

class SessionRequest(BaseModel):
    session_id: str

class DocumentRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = None
    deep_search: bool = False

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
    """Send a message and get AI response"""
    session_id = request.session_id or "default"
    
    try:
        if request.use_rag:
            # Use RAG service for enhanced responses
            result = await rag_service.rag_query(request.message, session_id)
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            
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
        else:
            # Use basic Ollama service with enhanced prompting
            from backend.services.prompt_service import prompt_service
            enhanced_prompt = prompt_service.build_basic_chat_prompt(request.message)
            response = await ollama_service.generate(enhanced_prompt)
            
            return {
                "success": True,
                "user_message": {
                    "id": str(uuid.uuid4()),
                    "content": request.message,
                    "timestamp": datetime.now().isoformat()
                },
                "assistant_message": {
                    "id": str(uuid.uuid4()),
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def stream_chat(request: ChatRequest):
    """Stream chat response using Server-Sent Events"""
    try:
        async def generate_response():
            try:
                # Use RAG service for enhanced responses
                result = await rag_service.rag_query(request.message)
                
                if result["success"] and result.get("response"):
                    # Stream the response
                    response_text = result["response"]
                    
                    # Send context information first
                    if result.get("context"):
                        context_info = {
                            "type": "context",
                            "sources": [doc.get("filename", "Unknown") for doc in result["context"]],
                            "context_files": result.get("context_files", [])
                        }
                        yield {
                            "event": "context",
                            "data": json.dumps(context_info)
                        }
                    
                    # Stream the response text
                    for i in range(0, len(response_text), 10):  # Send in chunks of 10 characters
                        chunk = response_text[i:i+10]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.02)  # Smooth streaming effect
                    
                    # Send completion signal
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True
                        })
                    }
                else:
                    # Fallback to basic chat
                    enhanced_prompt = prompt_service.build_basic_chat_prompt(request.message)
                    
                    async for chunk in ollama_service.generate_stream(enhanced_prompt):
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.02)
                    
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
    """Stream chat response using LangChain with Server-Sent Events"""
    try:
        async def generate_response():
            try:
                # Use LangChain RAG service
                result = await langchain_rag_service.rag_query(request.message)
                
                if result["success"] and result.get("response"):
                    response_text = result["response"]
                    
                    # Send context information first
                    if result.get("context"):
                        context_info = {
                            "type": "context",
                            "sources": [doc.get("filename", "Unknown") for doc in result["context"]],
                            "context_files": result.get("context_files", [])
                        }
                        yield {
                            "event": "context",
                            "data": json.dumps(context_info)
                        }
                    
                    # Stream the response text
                    for i in range(0, len(response_text), 10):
                        chunk = response_text[i:i+10]
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.02)
                    
                    # Send completion signal
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": "",
                            "finished": True
                        })
                    }
                else:
                    # Fallback to basic streaming
                    enhanced_prompt = prompt_service.build_basic_chat_prompt(request.message)
                    
                    async for chunk in ollama_service.generate_stream(enhanced_prompt):
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "content": chunk,
                                "finished": False
                            })
                        }
                        await asyncio.sleep(0.02)
                    
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

@app.delete("/api/chat/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session"""
    result = chat_controller.clear_session(session_id)
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
        
        # Use LangChain RAG service
        if request.use_rag:
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
                raise HTTPException(status_code=500, detail=rag_result.get("error", "RAG query failed"))
        else:
            # Basic chat without RAG
            enhanced_prompt = prompt_service.build_basic_chat_prompt(request.message)
            response_text = await ollama_service.generate(enhanced_prompt)
            
            assistant_message = {
                "id": assistant_message_id,
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "context": [],
                "metadata": {
                    "context_count": 0,
                    "fallback_mode": True,
                    "langchain_mode": False
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
@app.post("/api/vector/search")
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

# File upload endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process file"""
    try:
        # Read file content
        content = await file.read()
        
        # Extract text from file using file processing service
        extraction_result = FileProcessingService.extract_text_from_file(
            content, file.filename, file.content_type
        )
        
        if not extraction_result["text"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to extract text from {file.filename}: {extraction_result['metadata'].get('error', 'Unknown error')}"
            )
        
        # Add to knowledge base
        doc_id = await rag_service.add_document(
            extraction_result["text"],
            extraction_result["metadata"]
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "extracted_text_length": len(extraction_result["text"]),
            "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
            "message": "File uploaded and processed successfully"
        }
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# LangChain file upload endpoint
@app.post("/api/langchain/upload")
async def upload_file_langchain(file: UploadFile = File(...)):
    """Upload and process file using LangChain"""
    try:
        # Read file content
        content = await file.read()
        
        # Extract text from file using file processing service
        extraction_result = FileProcessingService.extract_text_from_file(
            content, file.filename, file.content_type
        )
        
        if not extraction_result["text"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to extract text from {file.filename}: {extraction_result['metadata'].get('error', 'Unknown error')}"
            )
        
        # Add to LangChain knowledge base
        doc_ids = await langchain_rag_service.add_document(
            extraction_result["text"],
            extraction_result["metadata"]
        )
        
        return {
            "success": True,
            "document_ids": doc_ids,
            "filename": file.filename,
            "size": len(content),
            "extracted_text_length": len(extraction_result["text"]),
            "extraction_method": extraction_result["metadata"].get("extraction_method", "unknown"),
            "message": "File uploaded and processed successfully with LangChain"
        }
    except Exception as e:
        logger.error(f"LangChain file upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Multiple files upload endpoint
@app.post("/api/upload/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload and process multiple files"""
    try:
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
                
                # Add to knowledge base
                doc_id = await rag_service.add_document(
                    extraction_result["text"],
                    extraction_result["metadata"]
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
            "message": f"Processed {len(files)} files: {successful_uploads} successful, {len(files) - successful_uploads} failed"
        }
        
    except Exception as e:
        logger.error(f"Multiple file upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# LangChain multiple files upload endpoint
@app.post("/api/langchain/upload/multiple")
async def upload_multiple_files_langchain(files: List[UploadFile] = File(...)):
    """Upload and process multiple files using LangChain"""
    try:
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
            "message": f"Processed {len(files)} files with LangChain: {successful_uploads} successful, {len(files) - successful_uploads} failed"
        }
        
    except Exception as e:
        logger.error(f"LangChain multiple file upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL_APP.lower()
    )
