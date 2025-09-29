"""
LangChain-based Vector Store service for PostgreSQL + pgvector
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.documents import Document
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
import httpx
import asyncio
from typing import List

from backend.config.settings import settings
from backend.services.database_service import db_service

logger = logging.getLogger(__name__)

class CustomOllamaEmbeddings(Embeddings):
    """Custom Ollama embeddings class that uses the correct API endpoint"""
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=60.0
        )
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents asynchronously"""
        embeddings = []
        for text in texts:
            embedding = await self._get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    async def aembed_query(self, text: str) -> List[float]:
        """Embed a single query asynchronously"""
        return await self._get_embedding(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents synchronously"""
        return asyncio.run(self.aembed_documents(texts))
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query synchronously"""
        return asyncio.run(self.aembed_query(text))
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        try:
            response = await self.client.post(
                "/api/embeddings",
                json={
                    "model": self.model,
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
            logger.error(f"Failed to get embedding: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class LangChainVectorService:
    """LangChain-based vector store service using PostgreSQL + pgvector"""
    
    def __init__(self):
        self.documents = None
        self.embeddings = None
        self.text_splitter = None
        
    async def initialize(self):
        """Initialize LangChain vector service"""
        try:
            # Initialize custom Ollama embeddings with correct API endpoint
            self.embeddings = CustomOllamaEmbeddings(
                model=settings.OLLAMA_EMBEDDING_MODEL,
                base_url=settings.OLLAMA_BASE_URL
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Initialize PGVector store
            # Use psycopg2 for LangChain PGVector compatibility
            connection_string = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
            
            self.documents = PGVector(
                connection_string=connection_string,
                embedding_function=self.embeddings,
                collection_name="langchain_documents",
                distance_strategy="cosine",
                use_jsonb=True  # Use JSONB for metadata to avoid deprecation warning
            )
            
            logger.info("LangChain vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain vector service: {e}")
            raise
    
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """Add document to vector store using LangChain"""
        try:
            if not self.documents:
                raise Exception("Vector store not initialized")
            
            logger.info(f"Starting document processing: {len(content)} characters")
            
            # Create document
            doc = Document(
                page_content=content,
                metadata=metadata or {}
            )
            
            # Split document into chunks
            logger.info("Splitting document into chunks...")
            chunks = self.text_splitter.split_documents([doc])
            logger.info(f"Document split into {len(chunks)} chunks")
            
            # Add chunks to vector store
            logger.info("Adding chunks to vector store...")
            doc_ids = await self.documents.aadd_documents(chunks)
            logger.info(f"Successfully added {len(doc_ids)} document chunks to vector store")
            
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    async def search_similar_optimized(self, query: str, top_k: int = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """최적화된 벡터 검색 with 캐싱 (LangChain 버전)"""
        try:
            if not self.documents:
                raise Exception("Vector store not initialized")
            
            # Use settings defaults if not provided
            top_k = top_k or settings.VECTOR_DB_TOP_K
            similarity_threshold = similarity_threshold or settings.VECTOR_DB_SIMILARITY_THRESHOLD
            
            # Search similar documents
            # Handle async method properly - await the coroutine
            docs_with_scores = await self.documents.asimilarity_search_with_score(
                query=query,
                k=top_k
            )
            
            # Filter by similarity threshold and format results
            documents = []
            for doc, score in docs_with_scores:
                # Convert distance to similarity (1 - distance for cosine similarity)
                # For cosine distance, score ranges from 0 to 2, where 0 means identical
                similarity = 1 - (score / 2)
                
                # Ensure similarity is between 0 and 1
                similarity = max(0.0, min(1.0, similarity))
                
                if similarity >= similarity_threshold:
                    documents.append({
                        "id": doc.metadata.get("id", ""),
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": similarity
                    })
            
            logger.info(f"Found {len(documents)} similar documents (LangChain optimized)")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search similar documents (LangChain optimized): {e}")
            raise

    async def search_similar(self, query: str, top_k: int = None, similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """Search for similar documents using LangChain"""
        try:
            if not self.documents:
                raise Exception("Vector store not initialized")
            
            # Use settings defaults if not provided
            top_k = top_k or settings.VECTOR_DB_TOP_K
            similarity_threshold = similarity_threshold or settings.VECTOR_DB_SIMILARITY_THRESHOLD
            
            # Search similar documents
            # Handle async method properly - await the coroutine
            docs_with_scores = await self.documents.asimilarity_search_with_score(
                query=query,
                k=top_k
            )
            
            # Filter by similarity threshold and format results
            documents = []
            for doc, score in docs_with_scores:
                # Convert distance to similarity (1 - distance for cosine similarity)
                # For cosine distance, score ranges from 0 to 2, where 0 means identical
                similarity = 1 - (score / 2)
                
                # Ensure similarity is between 0 and 1
                similarity = max(0.0, min(1.0, similarity))
                
                if similarity >= similarity_threshold:
                    documents.append({
                        "id": doc.metadata.get("id", ""),
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": similarity
                    })
            
            logger.info(f"Found {len(documents)} similar documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            if not self.documents:
                raise Exception("Vector store not initialized")
            
            # Search by metadata ID
            docs = await self.documents.asimilarity_search(
                query="",  # Empty query to get all documents
                k=1000,  # Large number to get all documents
                filter={"id": doc_id}
            )
            
            if docs:
                doc = docs[0]
                return {
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document by ID"""
        try:
            if not self.documents:
                raise Exception("Vector store not initialized")
            
            # Note: PGVector doesn't have a direct delete method
            # We'll need to use raw SQL for deletion
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            session = db_service.get_session()
            async with session:
                result = await session.execute(
                    text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'id' = :doc_id"),
                    {"doc_id": doc_id}
                )
                await session.commit()
                
                deleted_count = result.rowcount
                logger.info(f"Deleted {deleted_count} document chunks")
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    async def get_document_count(self) -> int:
        """Get total document count"""
        try:
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            session = db_service.get_session()
            async with session:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM langchain_pg_embedding")
                )
                count = result.scalar()
                return count or 0
                
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            raise
    
    async def get_collections(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get list of available collections for a specific user"""
        try:
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            session = db_service.get_session()
            async with session:
                collections = []
                
                # Always include the default 'langchain_documents' collection (shared)
                default_collection = {
                    "id": "default",
                    "name": "langchain_documents",
                    "metadata": {},
                    "created_at": None,
                    "document_count": 0,
                    "user_id": None  # Shared collection
                }
                
                # Count documents in default collection (all documents)
                doc_count_result = await session.execute(text("""
                    SELECT COUNT(*) 
                    FROM langchain_pg_embedding
                """))
                default_collection["document_count"] = doc_count_result.scalar() or 0
                
                # Add default collection
                collections.append(default_collection)
                
                # Get collections from langchain_pg_collection table with user filter
                if user_id:
                    result = await session.execute(text("""
                        SELECT 
                            uuid,
                            name,
                            cmetadata,
                            user_id
                        FROM langchain_pg_collection 
                        WHERE user_id = :user_id OR (cmetadata->>'is_shared')::boolean = true
                        ORDER BY name
                    """), {"user_id": user_id})
                else:
                    result = await session.execute(text("""
                        SELECT 
                            uuid,
                            name,
                            cmetadata,
                            user_id
                        FROM langchain_pg_collection 
                        ORDER BY name
                    """))
                
                for row in result:
                    metadata = row.cmetadata or {}
                    is_shared = metadata.get("is_shared", False)
                    
                    collection = {
                        "id": str(row.uuid),
                        "name": row.name,
                        "metadata": metadata,
                        "created_at": None,
                        "document_count": 0,
                        "user_id": row.user_id,
                        "is_shared": is_shared,
                        "created_by": metadata.get("created_by", row.user_id)
                    }
                    
                    # Count documents in this collection
                    doc_count_result = await session.execute(text("""
                        SELECT COUNT(*) 
                        FROM langchain_pg_embedding 
                        WHERE collection_id = :collection_id
                    """), {"collection_id": collection["id"]})
                    
                    collection["document_count"] = doc_count_result.scalar() or 0
                    collections.append(collection)
                
                logger.info(f"Found {len(collections)} collections for user {user_id}")
                return collections
                
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            # Return default collection even if there's an error
            return [{
                "id": "default",
                "name": "langchain_documents",
                "metadata": {},
                "created_at": None,
                "document_count": 0
            }]
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific collection"""
        try:
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            session = db_service.get_session()
            async with session:
                # Handle default 'langchain_documents' collection
                if collection_name == "langchain_documents":
                    # Count documents in default collection (all documents)
                    doc_count_result = await session.execute(text("""
                        SELECT COUNT(*) 
                        FROM langchain_pg_embedding
                    """))
                    
                    doc_count = doc_count_result.scalar() or 0
                    
                    # Get sample documents from default collection
                    sample_docs_result = await session.execute(text("""
                        SELECT 
                            document,
                            cmetadata
                        FROM langchain_pg_embedding 
                        LIMIT 5
                    """))
                    
                    sample_documents = []
                    for doc_row in sample_docs_result:
                        sample_documents.append({
                            "content": doc_row.document[:200] + "..." if len(doc_row.document) > 200 else doc_row.document,
                            "metadata": doc_row.cmetadata or {}
                        })
                    
                    return {
                        "id": "default",
                        "name": "langchain_documents",
                        "metadata": {},
                        "created_at": None,
                        "document_count": doc_count,
                        "sample_documents": sample_documents
                    }
                
                # Get collection details from langchain_pg_collection table
                result = await session.execute(text("""
                    SELECT 
                        uuid,
                        name,
                        cmetadata
                    FROM langchain_pg_collection 
                    WHERE name = :collection_name
                """), {"collection_name": collection_name})
                
                row = result.fetchone()
                if not row:
                    raise Exception(f"Collection '{collection_name}' not found")
                
                # Get document count and sample documents
                doc_count_result = await session.execute(text("""
                    SELECT COUNT(*) 
                    FROM langchain_pg_embedding 
                    WHERE collection_id = :collection_id
                """), {"collection_id": str(row.uuid)})
                
                doc_count = doc_count_result.scalar() or 0
                
                # Get sample documents
                sample_docs_result = await session.execute(text("""
                    SELECT 
                        document,
                        cmetadata
                    FROM langchain_pg_embedding 
                    WHERE collection_id = :collection_id
                    LIMIT 5
                """), {"collection_id": str(row.uuid)})
                
                sample_documents = []
                for doc_row in sample_docs_result:
                    sample_documents.append({
                        "content": doc_row.document[:200] + "..." if len(doc_row.document) > 200 else doc_row.document,
                        "metadata": doc_row.cmetadata or {}
                    })
                
                return {
                    "id": str(row.uuid),
                    "name": row.name,
                    "metadata": row.cmetadata or {},
                    "created_at": None,
                    "document_count": doc_count,
                    "sample_documents": sample_documents
                }
                
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise
    
    async def create_collection(self, collection_name: str, description: str = "", user_id: str = None, is_shared: bool = False) -> Dict[str, Any]:
        """Create a new collection for a specific user"""
        try:
            if not collection_name or collection_name.strip() == "":
                raise ValueError("Collection name cannot be empty")
            
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            # Check if collection already exists for this user
            existing_collections = await self.get_collections(user_id)
            for collection in existing_collections:
                if collection["name"] == collection_name:
                    raise ValueError(f"Collection '{collection_name}' already exists")
            
            # Create collection in langchain_pg_collection table with user_id
            collection_uuid = str(uuid.uuid4())
            async with db_service.get_session() as session:
                result = await session.execute(
                    text("""
                        INSERT INTO langchain_pg_collection (uuid, name, cmetadata, user_id)
                        VALUES (:uuid, :name, :metadata, :user_id)
                        RETURNING uuid, name, cmetadata, user_id
                    """),
                    {
                        "uuid": collection_uuid,
                        "name": collection_name,
                        "metadata": json.dumps({
                            "description": description, 
                            "created_by": user_id or "system",
                            "is_shared": is_shared
                        }),
                        "user_id": user_id
                    }
                )
                row = result.fetchone()
                
                if not row:
                    raise Exception("Failed to create collection")
                
                # Commit the transaction
                await session.commit()
                
                logger.info(f"Created collection: {collection_name}")
                return {
                    "id": str(row.uuid),
                    "name": row.name,
                    "description": description,
                    "created_at": None,
                    "document_count": 0,
                    "status": "created"
                }
                
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise
    
    async def delete_collection(self, collection_name: str, user_id: str = None) -> Dict[str, Any]:
        """Delete a collection and all its documents"""
        try:
            if collection_name == "langchain_documents":
                raise ValueError("Cannot delete the default 'langchain_documents' collection")
            
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            # Check if collection exists and verify user ownership
            collections = await self.get_collections(user_id)
            collection_exists = any(c["name"] == collection_name for c in collections)
            
            if not collection_exists:
                logger.info(f"Collection '{collection_name}' does not exist, skipping deletion")
                raise ValueError(f"Collection '{collection_name}' does not exist")
            
            async with db_service.get_session() as session:
                # Get collection UUID and user_id
                result = await session.execute(
                    text("SELECT uuid, user_id FROM langchain_pg_collection WHERE name = :name"),
                    {"name": collection_name}
                )
                row = result.fetchone()
                
                if not row:
                    raise ValueError(f"Collection '{collection_name}' not found")
                
                collection_uuid = row.uuid
                collection_user_id = row.user_id
                
                # Check user authorization - only the creator can delete the collection
                if user_id and collection_user_id is not None and collection_user_id != user_id:
                    raise ValueError(f"You are not authorized to delete collection '{collection_name}'. Only the collection owner can delete it.")
                elif user_id and collection_user_id is None:
                    # Shared collections (user_id = NULL) - check created_by in metadata
                    metadata = row.cmetadata or {}
                    created_by = metadata.get("created_by")
                    if created_by != user_id:
                        raise ValueError(f"You are not authorized to delete collection '{collection_name}'. Only the collection owner can delete it.")
                
                # Delete all documents in the collection
                await session.execute(
                    text("DELETE FROM langchain_pg_embedding WHERE collection_id = :collection_id"),
                    {"collection_id": collection_uuid}
                )
                
                # Delete the collection
                await session.execute(
                    text("DELETE FROM langchain_pg_collection WHERE uuid = :uuid"),
                    {"uuid": collection_uuid}
                )
                
                await session.commit()
                
                logger.info(f"Deleted collection: {collection_name}")
                return {
                    "name": collection_name,
                    "status": "deleted",
                    "message": f"Collection '{collection_name}' and all its documents have been deleted"
                }
                
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            raise
    
    async def rename_collection(self, old_name: str, new_name: str, user_id: str = None) -> Dict[str, Any]:
        """Rename a collection"""
        try:
            if old_name == "langchain_documents":
                raise ValueError("Cannot rename the default 'langchain_documents' collection")
            
            if not new_name or new_name.strip() == "":
                raise ValueError("New collection name cannot be empty")
            
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            # Check if old collection exists and verify user ownership
            collections = await self.get_collections(user_id)
            old_exists = any(c["name"] == old_name for c in collections)
            if not old_exists:
                raise ValueError(f"Collection '{old_name}' does not exist")
            
            # Check if new name already exists
            new_exists = any(c["name"] == new_name for c in collections)
            if new_exists:
                raise ValueError(f"Collection '{new_name}' already exists")
            
            async with db_service.get_session() as session:
                # Get collection info and verify ownership
                result = await session.execute(
                    text("SELECT uuid, user_id FROM langchain_pg_collection WHERE name = :old_name"),
                    {"old_name": old_name}
                )
                row = result.fetchone()
                
                if not row:
                    raise ValueError(f"Collection '{old_name}' not found")
                
                collection_user_id = row.user_id
                
                # Check user authorization - only the creator can rename the collection
                if user_id and collection_user_id is not None and collection_user_id != user_id:
                    raise ValueError(f"You are not authorized to rename collection '{old_name}'. Only the collection owner can rename it.")
                elif user_id and collection_user_id is None:
                    # Shared collections (user_id = NULL) - check created_by in metadata
                    metadata = row.cmetadata or {}
                    created_by = metadata.get("created_by")
                    if created_by != user_id:
                        raise ValueError(f"You are not authorized to rename collection '{old_name}'. Only the collection owner can rename it.")
                
                # Update collection name
                result = await session.execute(
                    text("""
                        UPDATE langchain_pg_collection 
                        SET name = :new_name 
                        WHERE name = :old_name
                        RETURNING uuid, name
                    """),
                    {"old_name": old_name, "new_name": new_name}
                )
                row = result.fetchone()
                
                if not row:
                    raise ValueError(f"Collection '{old_name}' not found")
                
                await session.commit()
                
                logger.info(f"Renamed collection from '{old_name}' to '{new_name}'")
                return {
                    "old_name": old_name,
                    "new_name": new_name,
                    "status": "renamed",
                    "message": f"Collection renamed from '{old_name}' to '{new_name}'"
                }
                
        except Exception as e:
            logger.error(f"Failed to rename collection from '{old_name}' to '{new_name}': {e}")
            raise
    
    async def change_collection_type(self, collection_name: str, new_user_id: str = None) -> Dict[str, Any]:
        """Change collection type between personal and shared"""
        try:
            if collection_name == "langchain_documents":
                raise ValueError("Cannot change type of the default 'langchain_documents' collection")
            
            # Ensure database service is initialized
            if not hasattr(db_service, 'async_session_factory') or not db_service.async_session_factory:
                logger.info("Database not initialized, initializing...")
                await db_service.initialize()
            
            async with db_service.get_session() as session:
                # Update collection user_id and metadata
                # For shared collections: keep original user_id but set is_shared=True
                # For personal collections: set user_id to current user and is_shared=False
                is_shared = (new_user_id is None)
                
                # For shared collections, keep the original user_id in metadata
                if is_shared:
                    # Get current user_id to store in metadata
                    current_result = await session.execute(text("""
                        SELECT user_id FROM langchain_pg_collection WHERE name = :collection_name
                    """), {"collection_name": collection_name})
                    current_row = current_result.fetchone()
                    original_user_id = current_row.user_id if current_row else None
                    
                    result = await session.execute(text("""
                        UPDATE langchain_pg_collection 
                        SET user_id = NULL,
                            cmetadata = jsonb_set(
                                jsonb_set(cmetadata, '{is_shared}', :is_shared::jsonb),
                                '{created_by}', :created_by::jsonb
                            )
                        WHERE name = :collection_name
                    """), {
                        "collection_name": collection_name,
                        "is_shared": json.dumps(is_shared),
                        "created_by": json.dumps(original_user_id or "system")
                    })
                else:
                    result = await session.execute(text("""
                        UPDATE langchain_pg_collection 
                        SET user_id = :new_user_id,
                            cmetadata = jsonb_set(cmetadata, '{is_shared}', :is_shared::jsonb)
                        WHERE name = :collection_name
                    """), {
                        "new_user_id": new_user_id, 
                        "collection_name": collection_name,
                        "is_shared": json.dumps(is_shared)
                    })
                
                if result.rowcount == 0:
                    raise ValueError(f"Collection '{collection_name}' not found")
                
                await session.commit()
                
                type_text = "개인" if new_user_id else "공유"
                logger.info(f"Collection '{collection_name}' changed to {type_text} collection")
                
                return {
                    "success": True,
                    "message": f"Collection '{collection_name}' changed to {type_text} collection",
                    "collection_name": collection_name,
                    "user_id": new_user_id,
                    "type": type_text
                }
                
        except Exception as e:
            logger.error(f"Failed to change collection type: {e}")
            raise
    
    async def set_collection(self, collection_name: str) -> bool:
        """Switch to a different collection"""
        try:
            # Initialize PGVector store with new collection
            connection_string = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
            
            self.documents = PGVector(
                connection_string=connection_string,
                embedding_function=self.embeddings,
                collection_name=collection_name,
                distance_strategy="cosine",
                use_jsonb=True  # Use JSONB for metadata to avoid deprecation warning
            )
            
            logger.info(f"Switched to collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set collection '{collection_name}': {e}")
            return False

    async def close(self):
        """Close vector service"""
        try:
            if self.embeddings and hasattr(self.embeddings, 'close'):
                await self.embeddings.close()
            if self.documents:
                # PGVector doesn't have a close method
                pass
            logger.info("LangChain vector service closed")
        except Exception as e:
            logger.error(f"Failed to close vector service: {e}")

# Global LangChain vector service instance
langchain_vector_service = LangChainVectorService()
