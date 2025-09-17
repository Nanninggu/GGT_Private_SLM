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
    
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None, collection_name: Optional[str] = None) -> str:
        """Add document to vector database"""
        try:
            # Ensure service is initialized
            if not self.ollama_client:
                await self.initialize()
            
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
                        INSERT INTO documents (id, content, metadata, embedding, collection_name)
                        VALUES (gen_random_uuid(), :content, :metadata, :embedding, :collection_name)
                        RETURNING id
                    """),
                    {
                        "content": content,
                        "metadata": json.dumps(metadata or {}),
                        "embedding": str(embedding),
                        "collection_name": collection_name
                    }
                )
                doc_id = result.scalar()
                await session.commit()
                
                logger.info(f"Document added with ID: {doc_id} to collection: {collection_name}")
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
    
    # Collection management methods
    async def create_collection(self, collection_name: str) -> bool:
        """Create a new collection (just a logical grouping, no separate table needed)"""
        try:
            # Collections are logical groupings, we just need to ensure the collection_name column exists
            # and return success
            logger.info(f"Collection '{collection_name}' is ready for use")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    async def get_collection(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        try:
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                await db_service.initialize()
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT 
                            collection_name,
                            COUNT(*) as document_count,
                            MIN(created_at) as created_at,
                            MAX(created_at) as updated_at
                        FROM documents 
                        WHERE collection_name = :collection_name
                        GROUP BY collection_name
                    """),
                    {"collection_name": collection_name}
                )
                
                row = result.fetchone()
                if row:
                    return {
                        "name": row.collection_name,
                        "document_count": row.document_count,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    }
                else:
                    # Collection doesn't exist yet, but we can create it
                    return {
                        "name": collection_name,
                        "document_count": 0,
                        "created_at": None,
                        "updated_at": None
                    }
        except Exception as e:
            logger.error(f"Failed to get collection: {e}")
            raise
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections"""
        try:
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                await db_service.initialize()
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT 
                            collection_name,
                            COUNT(*) as document_count,
                            MIN(created_at) as created_at,
                            MAX(created_at) as updated_at
                        FROM documents 
                        WHERE collection_name IS NOT NULL
                        GROUP BY collection_name
                        ORDER BY collection_name
                    """)
                )
                
                collections = []
                for row in result:
                    collections.append({
                        "name": row.collection_name,
                        "document_count": row.document_count,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    })
                
                return collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection and all its documents"""
        try:
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                await db_service.initialize()
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("DELETE FROM documents WHERE collection_name = :collection_name"),
                    {"collection_name": collection_name}
                )
                await session.commit()
                
                deleted_count = result.rowcount
                logger.info(f"Deleted collection '{collection_name}' with {deleted_count} documents")
                return deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise
    
    async def search_similar_in_collection(self, query: str, collection_name: str, top_k: int = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """Search for similar documents within a specific collection"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Use settings defaults if not provided
            top_k = top_k or settings.VECTOR_DB_TOP_K
            similarity_threshold = similarity_threshold or settings.VECTOR_DB_SIMILARITY_THRESHOLD
            
            # Search similar documents in collection
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
                            collection_name,
                            1 - (embedding <=> :query_embedding) as similarity
                        FROM documents
                        WHERE collection_name = :collection_name
                        AND 1 - (embedding <=> :query_embedding) > :similarity_threshold
                        ORDER BY embedding <=> :query_embedding
                        LIMIT :top_k
                    """),
                    {
                        "query_embedding": str(query_embedding),
                        "collection_name": collection_name,
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
                        "collection_name": row.collection_name,
                        "similarity": float(row.similarity)
                    })
                
                logger.info(f"Found {len(documents)} similar documents in collection '{collection_name}'")
                return documents
                
        except Exception as e:
            logger.error(f"Failed to search similar documents in collection: {e}")
            raise

    async def get_collections(self) -> List[Dict[str, Any]]:
        """Get list of available collections from documents table"""
        try:
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                await db_service.initialize()
            
            async with db_service.get_session() as session:
                # Get unique collection names and their document counts
                result = await session.execute(text("""
                    SELECT 
                        collection_name,
                        COUNT(*) as document_count
                    FROM documents 
                    WHERE collection_name IS NOT NULL
                    GROUP BY collection_name
                    ORDER BY collection_name
                """))
                
                collections = []
                for row in result:
                    collections.append({
                        "id": f"basic_rag_{row.collection_name}",
                        "name": row.collection_name,
                        "metadata": {},
                        "created_at": None,
                        "document_count": row.document_count
                    })
                
                # Always include the default 'documents' collection
                if not any(c["name"] == "documents" for c in collections):
                    # Get count for documents collection (NULL collection_name)
                    null_count_result = await session.execute(text("SELECT COUNT(*) FROM documents WHERE collection_name IS NULL"))
                    null_count = null_count_result.scalar() or 0
                    
                    collections.insert(0, {
                        "id": "basic_rag_documents",
                        "name": "documents",
                        "metadata": {},
                        "created_at": None,
                        "document_count": null_count
                    })
                
                return collections
                
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            # Return default collection even if there's an error
            return [{
                "id": "basic_rag_documents",
                "name": "documents",
                "metadata": {},
                "created_at": None,
                "document_count": 0
            }]
    
    async def close(self):
        """Close vector service"""
        if self.ollama_client:
            await self.ollama_client.aclose()
            logger.info("Vector service closed")

# Global vector service instance
vector_service = VectorService()
