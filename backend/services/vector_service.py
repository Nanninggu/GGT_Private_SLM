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
from backend.services.cache_service import cache_service

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
        """Generate embedding using Ollama with caching"""
        try:
            # Check cache first
            cached_embedding = await cache_service.get_embedding(text)
            if cached_embedding:
                logger.debug("Embedding cache hit")
                return cached_embedding
            
            # Generate new embedding
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
            embedding = data["embedding"]
            
            # Cache the embedding
            await cache_service.set_embedding(text, embedding)
            
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def add_documents_batch(self, documents: List[Dict[str, Any]], 
                                batch_size: int = None) -> List[str]:
        """배치 처리로 문서 추가 최적화"""
        try:
            batch_size = batch_size or settings.VECTOR_DB_BATCH_SIZE
            doc_ids = []
            
            # Ensure service is initialized
            if not self.ollama_client:
                await self.initialize()
            
            # Process documents in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
                
                # Generate embeddings for batch
                embeddings = await asyncio.gather(*[
                    self.generate_embedding(doc['content']) for doc in batch
                ])
                
                # Batch insert to database
                if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                    await db_service.initialize()
                
                async with db_service.get_session() as session:
                    values = []
                    for doc, embedding in zip(batch, embeddings):
                        values.append({
                            "content": doc['content'],
                            "metadata": json.dumps(doc.get('metadata', {})),
                            "embedding": str(embedding),
                            "collection_name": doc.get('collection_name')
                        })
                    
                    # Use executemany for batch insert
                    result = await session.execute(
                        text("""
                            INSERT INTO documents (content, metadata, embedding, collection_name)
                            VALUES (:content, :metadata, :embedding, :collection_name)
                            RETURNING id
                        """),
                        values
                    )
                    
                    batch_ids = [str(row.id) for row in result]
                    doc_ids.extend(batch_ids)
                    await session.commit()
                    
                    logger.info(f"Added {len(batch_ids)} documents in batch")
            
            logger.info(f"Successfully added {len(doc_ids)} documents in batches")
            return doc_ids
                
        except Exception as e:
            logger.error(f"Failed to add documents in batch: {e}")
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
    
    async def search_similar_optimized(self, query: str, top_k: int = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """최적화된 벡터 검색 with PostgreSQL 설정 적용 및 캐싱"""
        try:
            # Use settings defaults if not provided
            top_k = top_k or settings.VECTOR_DB_TOP_K
            similarity_threshold = similarity_threshold or settings.VECTOR_DB_SIMILARITY_THRESHOLD
            
            # Check cache first
            cached_results = await cache_service.get_search_results(query, top_k, similarity_threshold)
            if cached_results:
                logger.debug("Search cache hit")
                return cached_results
            
            # Generate query embedding with caching
            query_embedding = await self.generate_embedding(query)
            
            # Search similar documents with optimization
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.error(f"Database not initialized. async_session_factory: {getattr(db_service, 'async_session_factory', 'Not found')}")
                # Try to initialize database service
                await db_service.initialize()
                if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                    logger.warning("Database not available, returning empty results")
                    return []
            
            async with db_service.get_session() as session:
                # Apply PostgreSQL optimization settings
                await session.execute(text(f"SET hnsw.ef_search = {settings.VECTOR_DB_EF_SEARCH}"))
                
                # 최적화된 벡터 검색 쿼리 - 인덱스 힌트와 성능 최적화
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
                        "metadata": row.metadata if isinstance(row.metadata, dict) else (json.loads(row.metadata) if row.metadata else {}),
                        "similarity": float(row.similarity)
                    })
                
                # Cache the results
                await cache_service.set_search_results(query, top_k, similarity_threshold, documents)
                
                logger.info(f"Found {len(documents)} similar documents (optimized)")
                return documents
                
        except Exception as e:
            logger.error(f"Failed to search similar documents (optimized): {e}")
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
                        "metadata": row.metadata if isinstance(row.metadata, dict) else (json.loads(row.metadata) if row.metadata else {}),
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
                        "metadata": row.metadata if isinstance(row.metadata, dict) else (json.loads(row.metadata) if row.metadata else {}),
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
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """벡터 DB 성능 통계 및 캐시 통계"""
        try:
            # Get cache statistics
            cache_stats = cache_service.get_cache_stats()
            
            # Get database statistics
            db_stats = {}
            if hasattr(db_service, 'async_session_factory') and db_service.async_session_factory:
                async with db_service.get_session() as session:
                    # Document count
                    result = await session.execute(text("SELECT COUNT(*) FROM documents"))
                    db_stats["total_documents"] = result.scalar()
                    
                    # Index usage statistics
                    index_result = await session.execute(text("""
                        SELECT 
                            schemaname,
                            tablename,
                            indexname,
                            idx_scan,
                            idx_tup_read,
                            idx_tup_fetch
                        FROM pg_stat_user_indexes 
                        WHERE indexname LIKE '%embedding%' OR indexname LIKE '%documents%'
                    """))
                    db_stats["index_usage"] = [dict(row._mapping) for row in index_result]
                    
                    # Table size information
                    size_result = await session.execute(text("""
                        SELECT 
                            pg_size_pretty(pg_total_relation_size('documents')) as table_size,
                            pg_size_pretty(pg_relation_size('documents_embedding_idx')) as index_size
                    """))
                    size_row = size_result.fetchone()
                    if size_row:
                        db_stats["table_size"] = size_row.table_size
                        db_stats["index_size"] = size_row.index_size
            
            return {
                "cache_stats": cache_stats,
                "database_stats": db_stats,
                "vector_settings": {
                    "ef_construction": settings.VECTOR_DB_EF_CONSTRUCTION,
                    "ef_search": settings.VECTOR_DB_EF_SEARCH,
                    "m": settings.VECTOR_DB_M,
                    "similarity_threshold": settings.VECTOR_DB_SIMILARITY_THRESHOLD,
                    "top_k": settings.VECTOR_DB_TOP_K,
                    "batch_size": settings.VECTOR_DB_BATCH_SIZE
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}
    
    async def preload_common_embeddings(self, texts: List[str]):
        """일반적인 텍스트들의 임베딩 사전 로드"""
        try:
            await cache_service.preload_embeddings(texts, self.generate_embedding)
            logger.info(f"Preloaded {len(texts)} common embeddings")
        except Exception as e:
            logger.error(f"Failed to preload embeddings: {e}")
    
    async def close(self):
        """Close vector service"""
        if self.ollama_client:
            await self.ollama_client.aclose()
            logger.info("Vector service closed")

# Global vector service instance
vector_service = VectorService()
