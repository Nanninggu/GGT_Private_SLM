"""
Vector database service for pgvector integration
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import json

from backend.config.settings import settings
from backend.services.database_service import db_service

logger = logging.getLogger(__name__)

class VectorService:
    """Vector database service for similarity search and embeddings"""
    
    def __init__(self):
        self.ollama_client = None
        
    async def initialize(self):
        """Initialize vector service"""
        try:
            self.ollama_client = httpx.AsyncClient(
                base_url=settings.OLLAMA_BASE_URL,
                timeout=settings.OLLAMA_EMBEDDING_TIMEOUT
            )
            logger.info("Vector service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        try:
            response = await self.ollama_client.post(
                "/api/embeddings",
                json={
                    "model": settings.OLLAMA_EMBEDDING_MODEL,
                    "prompt": text,
                    "options": {
                        "num_ctx": settings.OLLAMA_EMBEDDING_NUM_CTX
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add document to vector database"""
        try:
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            # Store in database using existing documents table
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.error(f"Database not initialized. async_session_factory: {getattr(db_service, 'async_session_factory', 'Not found')}")
                # Try to initialize database service
                await db_service.initialize()
                if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                    raise Exception("Database not initialized. Please ensure database service is running.")
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("""
                        INSERT INTO documents (id, content, metadata, embedding)
                        VALUES (gen_random_uuid(), :content, :metadata, :embedding)
                        RETURNING id
                    """),
                    {
                        "content": content,
                        "metadata": json.dumps(metadata or {}),
                        "embedding": str(embedding)
                    }
                )
                doc_id = result.scalar()
                await session.commit()
                
                logger.info(f"Document added with ID: {doc_id}")
                return str(doc_id)
                
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    async def search_similar(self, query: str, top_k: int = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Use settings defaults if not provided
            top_k = top_k or settings.VECTOR_DB_TOP_K
            similarity_threshold = similarity_threshold or settings.VECTOR_DB_SIMILARITY_THRESHOLD
            
            # Search similar documents
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.error(f"Database not initialized. async_session_factory: {getattr(db_service, 'async_session_factory', 'Not found')}")
                # Try to initialize database service
                await db_service.initialize()
                if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                    logger.warning("Database not available, returning empty results")
                    return []
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT 
                            id,
                            content,
                            metadata,
                            1 - (embedding <=> :query_embedding) as similarity
                        FROM documents
                        WHERE 1 - (embedding <=> :query_embedding) > :similarity_threshold
                        ORDER BY embedding <=> :query_embedding
                        LIMIT :top_k
                    """),
                    {
                        "query_embedding": str(query_embedding),
                        "similarity_threshold": similarity_threshold,
                        "top_k": top_k
                    }
                )
                
                documents = []
                for row in result:
                    documents.append({
                        "id": str(row.id),
                        "content": row.content,
                        "metadata": json.loads(row.metadata) if row.metadata else {},
                        "similarity": float(row.similarity)
                    })
                
                logger.info(f"Found {len(documents)} similar documents")
                return documents
                
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT id, content, metadata
                        FROM documents
                        WHERE id = :doc_id
                    """),
                    {"doc_id": doc_id}
                )
                
                row = result.fetchone()
                if row:
                    return {
                        "id": str(row.id),
                        "content": row.content,
                        "metadata": json.loads(row.metadata) if row.metadata else {}
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document by ID"""
        try:
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("DELETE FROM documents WHERE id = :doc_id"),
                    {"doc_id": doc_id}
                )
                await session.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Document {doc_id} deleted successfully")
                else:
                    logger.warning(f"Document {doc_id} not found")
                
                return deleted
                
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    async def get_document_count(self) -> int:
        """Get total document count"""
        try:
            async with db_service.get_session() as session:
                result = await session.execute(text("SELECT COUNT(*) FROM documents"))
                count = result.scalar()
                return count
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            raise
    
    async def close(self):
        """Close vector service"""
        if self.ollama_client:
            await self.ollama_client.aclose()
            logger.info("Vector service closed")

# Global vector service instance
vector_service = VectorService()
