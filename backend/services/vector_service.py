"""
Vector database service for pgvector integration
"""
import asyncio
import logging
import re
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
                # Apply PostgreSQL optimization settings (추가 최적화)
                await session.execute(text(f"SET hnsw.ef_search = {settings.VECTOR_DB_EF_SEARCH}"))
                await session.execute(text("SET enable_seqscan = off"))  # Force index usage
                await session.execute(text("SET random_page_cost = 1.1"))  # SSD 최적화
                await session.execute(text("SET effective_cache_size = '4GB'"))  # 캐시 크기 최적화
                
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
                
                # Apply advanced filtering and ranking
                documents = self._apply_advanced_filtering(query, documents)
                
                # Cache the results
                await cache_service.set_search_results(query, top_k, similarity_threshold, documents)
                
                logger.info(f"Found {len(documents)} similar documents (ultra-optimized with filtering)")
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
    
    def _apply_advanced_filtering(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply advanced filtering and ranking to search results"""
        try:
            if not documents:
                return documents
            
            # Extract query keywords
            query_keywords = self._extract_keywords(query)
            
            # Apply content quality scoring
            for doc in documents:
                doc['content_quality_score'] = self._calculate_content_quality_score(doc['content'], query_keywords)
                doc['relevance_boost'] = self._calculate_relevance_boost(doc['content'], query)
            
            # Re-rank documents based on combined scores
            for doc in documents:
                # Combine similarity with content quality and relevance boost
                base_similarity = doc['similarity']
                content_quality = doc['content_quality_score']
                relevance_boost = doc['relevance_boost']
                
                # Weighted combination: 60% similarity + 25% content quality + 15% relevance boost
                doc['final_score'] = (
                    base_similarity * 0.6 +
                    content_quality * 0.25 +
                    relevance_boost * 0.15
                )
            
            # Sort by final score and remove duplicates
            documents = sorted(documents, key=lambda x: x['final_score'], reverse=True)
            documents = self._remove_duplicate_content(documents)
            
            # Apply diversity filtering to avoid similar documents
            documents = self._apply_diversity_filtering(documents)
            
            logger.info(f"Applied advanced filtering to {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to apply advanced filtering: {e}")
            return documents
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        
        # Remove common stop words
        stop_words = {'은', '는', '이', '가', '을', '를', '에', '의', '로', '으로', '와', '과', '도', '만', '부터', '까지', '에서', '에게', '한테', '께', '더', '가장', '매우', '정말', '진짜', '완전', '너무', '아주', '꽤', '상당히', '꽤나', '제법', '어느', '어떤', '무엇', '어디', '언제', '누가', '왜', '어떻게', '몇', '얼마', '얼마나'}
        
        # Extract Korean words (2+ characters)
        korean_words = re.findall(r'[가-힣]{2,}', query)
        
        # Filter out stop words and short words
        keywords = [word for word in korean_words if word not in stop_words and len(word) >= 2]
        
        return keywords
    
    def _calculate_content_quality_score(self, content: str, query_keywords: List[str]) -> float:
        """Calculate content quality score based on various factors"""
        try:
            score = 0.0
            
            # Length score (optimal length is 200-800 characters)
            content_length = len(content)
            if 200 <= content_length <= 800:
                score += 0.3
            elif 100 <= content_length <= 1000:
                score += 0.2
            else:
                score += 0.1
            
            # Keyword density score
            if query_keywords:
                keyword_matches = sum(1 for keyword in query_keywords if keyword in content)
                keyword_density = keyword_matches / len(query_keywords)
                score += keyword_density * 0.3
            
            # Structure score (check for organized content)
            structure_indicators = ['•', '1.', '2.', '3.', '-', '→', '▶', ':', ';']
            structure_count = sum(content.count(indicator) for indicator in structure_indicators)
            structure_score = min(1.0, structure_count / 5) * 0.2
            score += structure_score
            
            # Information density score (check for specific information)
            info_indicators = ['데이터', '통계', '분석', '결과', '연구', '조사', '예시', '사례', '방법', '절차']
            info_count = sum(1 for indicator in info_indicators if indicator in content)
            info_score = min(1.0, info_count / 3) * 0.2
            score += info_score
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Failed to calculate content quality score: {e}")
            return 0.5
    
    def _calculate_relevance_boost(self, content: str, query: str) -> float:
        """Calculate relevance boost based on query-content matching"""
        try:
            # Extract key terms from query
            query_terms = re.findall(r'\b\w+\b', query.lower())
            content_terms = re.findall(r'\b\w+\b', content.lower())
            
            # Calculate term overlap
            common_terms = set(query_terms) & set(content_terms)
            if len(query_terms) > 0:
                overlap_ratio = len(common_terms) / len(query_terms)
            else:
                overlap_ratio = 0.0
            
            # Check for direct question addressing
            question_patterns = [
                r"질문.*답변", r"문의.*응답", r"요청.*제공",
                r"궁금.*설명", r"알고.*싶", r"궁금.*것"
            ]
            direct_addressing = any(re.search(pattern, content) for pattern in question_patterns)
            
            # Calculate final relevance boost
            boost = overlap_ratio * 0.7 + (0.3 if direct_addressing else 0.0)
            return min(1.0, boost)
            
        except Exception as e:
            logger.error(f"Failed to calculate relevance boost: {e}")
            return 0.5
    
    def _remove_duplicate_content(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove documents with duplicate or very similar content"""
        try:
            unique_docs = []
            seen_content_hashes = set()
            
            for doc in documents:
                # Create content hash for duplicate detection
                content = doc['content']
                content_hash = hash(content[:200])  # Use first 200 chars as hash
                
                if content_hash not in seen_content_hashes:
                    unique_docs.append(doc)
                    seen_content_hashes.add(content_hash)
                else:
                    logger.debug(f"Removed duplicate document: {doc.get('id', 'unknown')}")
            
            return unique_docs
            
        except Exception as e:
            logger.error(f"Failed to remove duplicate content: {e}")
            return documents
    
    def _apply_diversity_filtering(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply diversity filtering to ensure varied content sources"""
        try:
            if len(documents) <= 3:
                return documents
            
            diverse_docs = []
            used_sources = set()
            
            for doc in documents:
                # Check source diversity
                metadata = doc.get('metadata', {})
                source = metadata.get('filename', metadata.get('file_name', 'unknown'))
                
                # If we haven't seen this source or it's been a while, include it
                if source not in used_sources or len(diverse_docs) % 2 == 0:
                    diverse_docs.append(doc)
                    used_sources.add(source)
                    
                    # Limit to prevent too many documents
                    if len(diverse_docs) >= 5:
                        break
            
            return diverse_docs
            
        except Exception as e:
            logger.error(f"Failed to apply diversity filtering: {e}")
            return documents

    async def close(self):
        """Close vector service"""
        if self.ollama_client:
            await self.ollama_client.aclose()
            logger.info("Vector service closed")

# Global vector service instance
vector_service = VectorService()
