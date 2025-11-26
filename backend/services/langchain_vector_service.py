"""
LangChain-based Vector Store service for PostgreSQL + pgvector
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import concurrent.futures

from langchain_core.documents import Document
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
import httpx
from typing import List

from backend.config.settings import settings
from backend.services.database_service import db_service

logger = logging.getLogger(__name__)

class CustomOllamaEmbeddings(Embeddings):
    """Custom Ollama embeddings class that uses the correct API endpoint"""
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.async_client = httpx.AsyncClient(
            base_url=base_url,
            timeout=60.0
        )
        # Synchronous client for use in sync methods (not bound to any event loop)
        self._sync_client = None
    
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
    
    def _get_sync_client(self):
        """Get or create synchronous HTTP client (not bound to event loop)"""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.base_url,
                timeout=60.0
            )
        return self._sync_client
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents synchronously using sync client"""
        embeddings = []
        for text in texts:
            embedding = self._get_embedding_sync(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query synchronously using sync client"""
        return self._get_embedding_sync(text)
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text (async)"""
        try:
            response = await self.async_client.post(
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
            logger.error(f"Failed to get embedding (async): {e}")
            raise
    
    def _get_embedding_sync(self, text: str) -> List[float]:
        """Get embedding for a single text (synchronous using sync client)"""
        try:
            client = self._get_sync_client()
            response = client.post(
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
            logger.error(f"Failed to get embedding (sync): {e}")
            raise
    
    async def close(self):
        """Close both HTTP clients"""
        if self.async_client:
            await self.async_client.aclose()
        if self._sync_client:
            self._sync_client.close()

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
                use_jsonb=True,  # Use JSONB for metadata to avoid deprecation warning
                pre_delete_collection=False  # Don't delete existing collection on init
            )
            
            logger.info("LangChain vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain vector service: {e}")
            raise
    
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None, collection_name: Optional[str] = None) -> List[str]:
        """Add document to vector store using LangChain"""
        try:
            # If collection_name is provided, ensure we're using the correct collection
            if collection_name:
                logger.info(f"Setting collection to '{collection_name}' before adding document")
                success = await self.set_collection(collection_name)
                if not success:
                    raise Exception(f"Failed to set collection to '{collection_name}'. Collection may not exist.")
            
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
            # With AUTOCOMMIT mode, changes are immediately persisted to the database
            logger.info(f"Adding chunks to vector store (collection: {collection_name or 'current'})...")
            doc_ids = await self.documents.aadd_documents(chunks)
            logger.info(f"Successfully added {len(doc_ids)} document chunks to vector store (AUTOCOMMIT mode)")
            
            # Give a small delay to ensure database has finished processing
            await asyncio.sleep(0.1)
            
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
                
                # First, find the actual UUID of 'langchain_documents' collection in the database
                langchain_docs_result = await session.execute(text("""
                    SELECT uuid, cmetadata
                    FROM langchain_pg_collection
                    WHERE name = 'langchain_documents'
                    LIMIT 1
                """))
                langchain_docs_row = langchain_docs_result.fetchone()
                
                # Default collection info
                default_collection = {
                    "id": "default",
                    "name": "langchain_documents",
                    "metadata": {},
                    "created_at": None,
                    "document_count": 0,
                    "user_id": None  # Shared collection
                }
                
                # Count documents in default collection using actual collection_id
                if langchain_docs_row:
                    default_collection["id"] = str(langchain_docs_row.uuid)
                    default_collection["metadata"] = langchain_docs_row.cmetadata or {}
                    
                    # Count only documents that belong to this specific collection
                    doc_count_result = await session.execute(text("""
                        SELECT COUNT(*) 
                        FROM langchain_pg_embedding
                        WHERE collection_id = CAST(:collection_id AS UUID)
                    """), {"collection_id": str(langchain_docs_row.uuid)})
                    default_collection["document_count"] = doc_count_result.scalar() or 0
                    
                    # Get created_at from the first document in this collection
                    created_at = None
                    if default_collection["document_count"] > 0:
                        try:
                            doc_metadata_result = await session.execute(text("""
                                SELECT cmetadata
                                FROM langchain_pg_embedding
                                WHERE collection_id = CAST(:collection_id AS UUID)
                                ORDER BY uuid ASC
                                LIMIT 1
                            """), {"collection_id": str(langchain_docs_row.uuid)})
                            
                            doc_metadata_row = doc_metadata_result.fetchone()
                            if doc_metadata_row and doc_metadata_row.cmetadata:
                                doc_metadata = doc_metadata_row.cmetadata
                                if isinstance(doc_metadata, str):
                                    try:
                                        doc_metadata = json.loads(doc_metadata)
                                    except:
                                        doc_metadata = {}
                                
                                if isinstance(doc_metadata, dict):
                                    created_at = (
                                        doc_metadata.get("created_at") or 
                                        doc_metadata.get("created_date") or 
                                        doc_metadata.get("upload_date") or
                                        doc_metadata.get("date") or
                                        doc_metadata.get("timestamp")
                                    )
                        except Exception as e:
                            logger.debug(f"Failed to get created_at from document metadata: {e}")
                    
                    default_collection["created_at"] = created_at
                else:
                    # langchain_documents collection doesn't exist yet, count is 0
                    logger.info("langchain_documents collection not found in database, will be created on first use")
                
                # Add default collection
                collections.append(default_collection)
                
                # Get collections from langchain_pg_collection table with user filter
                # Personal collections: user_id matches the current user
                # Shared collections: user_id is NULL (accessible by all users)
                if user_id:
                    result = await session.execute(text("""
                        SELECT 
                            uuid,
                            name,
                            cmetadata,
                            user_id
                        FROM langchain_pg_collection 
                        WHERE user_id = :user_id OR user_id IS NULL
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
                    # Shared collections have NULL user_id, personal collections have user_id set
                    is_shared = row.user_id is None
                    
                    collection = {
                        "id": str(row.uuid),
                        "name": row.name,
                        "metadata": metadata,
                        "created_at": None,
                        "document_count": 0,
                        "user_id": row.user_id,
                        "type": "shared" if is_shared else "personal",
                        "is_shared": is_shared,
                        "created_by": metadata.get("created_by", row.user_id)
                    }
                    
                    # Count documents in this collection
                    doc_count_result = await session.execute(text("""
                        SELECT COUNT(*) 
                        FROM langchain_pg_embedding 
                        WHERE collection_id = CAST(:collection_id AS UUID)
                    """), {"collection_id": collection["id"]})
                    
                    count = doc_count_result.scalar() or 0
                    logger.info(f"Collection {collection['name']} ({collection['id']}) has {count} documents")
                    collection["document_count"] = count
                    
                    # Get created_at from collection metadata first, then from documents
                    created_at = None
                    
                    # 1. Try to get from collection metadata
                    if isinstance(metadata, dict):
                        created_at = metadata.get("created_at") or metadata.get("created_date")
                    
                    # 2. If not in metadata, try to get from the oldest document's metadata
                    if not created_at and collection["document_count"] > 0:
                        try:
                            # Get the oldest document's metadata
                            doc_metadata_result = await session.execute(text("""
                                SELECT cmetadata
                                FROM langchain_pg_embedding 
                                WHERE collection_id = CAST(:collection_id AS UUID)
                                ORDER BY uuid ASC
                                LIMIT 1
                            """), {"collection_id": collection["id"]})
                            
                            doc_metadata_row = doc_metadata_result.fetchone()
                            if doc_metadata_row and doc_metadata_row.cmetadata:
                                doc_metadata = doc_metadata_row.cmetadata
                                if isinstance(doc_metadata, str):
                                    try:
                                        doc_metadata = json.loads(doc_metadata)
                                    except:
                                        doc_metadata = {}
                                
                                if isinstance(doc_metadata, dict):
                                    created_at = (
                                        doc_metadata.get("created_at") or 
                                        doc_metadata.get("created_date") or 
                                        doc_metadata.get("upload_date") or
                                        doc_metadata.get("date") or
                                        doc_metadata.get("timestamp")
                                    )
                        except Exception as e:
                            logger.debug(f"Failed to get created_at from document metadata: {e}")
                    
                    # 3. If still not found and collection has documents, 
                    # estimate creation date as the time when first document was likely added
                    # Since we can't extract timestamp from UUID v4, we'll use a fallback:
                    # For collections with documents but no metadata, we can't determine exact date
                    # So we'll leave it as None and let frontend show "알 수 없음"
                    # But for better UX, we could use collection UUID creation time if it's UUID v1
                    # However, most UUIDs are v4 (random), so we can't extract timestamp
                    
                    collection["created_at"] = created_at
                    
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
                    # First, find the actual UUID of 'langchain_documents' collection
                    langchain_docs_result = await session.execute(text("""
                        SELECT uuid, cmetadata
                        FROM langchain_pg_collection
                        WHERE name = 'langchain_documents'
                        LIMIT 1
                    """))
                    langchain_docs_row = langchain_docs_result.fetchone()
                    
                    if langchain_docs_row:
                        collection_uuid = str(langchain_docs_row.uuid)
                        
                        # Count documents in default collection using actual collection_id
                        doc_count_result = await session.execute(text("""
                            SELECT COUNT(*) 
                            FROM langchain_pg_embedding
                            WHERE collection_id = CAST(:collection_id AS UUID)
                        """), {"collection_id": collection_uuid})
                        
                        doc_count = doc_count_result.scalar() or 0
                        
                        # Get sample documents from this specific collection
                        sample_docs_result = await session.execute(text("""
                            SELECT 
                                document,
                                cmetadata
                            FROM langchain_pg_embedding 
                            WHERE collection_id = CAST(:collection_id AS UUID)
                            LIMIT 5
                        """), {"collection_id": collection_uuid})
                        
                        sample_documents = []
                        for doc_row in sample_docs_result:
                            sample_documents.append({
                                "content": doc_row.document[:200] + "..." if len(doc_row.document) > 200 else doc_row.document,
                                "metadata": doc_row.cmetadata or {}
                            })
                        
                        return {
                            "id": collection_uuid,
                            "name": "langchain_documents",
                            "metadata": langchain_docs_row.cmetadata or {},
                            "created_at": None,
                            "document_count": doc_count,
                            "sample_documents": sample_documents
                        }
                    else:
                        # Collection doesn't exist yet
                        return {
                            "id": "default",
                            "name": "langchain_documents",
                            "metadata": {},
                            "created_at": None,
                            "document_count": 0,
                            "sample_documents": []
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
                
                metadata = row.cmetadata or {}
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                # Get document count and sample documents
                doc_count_result = await session.execute(text("""
                    SELECT COUNT(*) 
                    FROM langchain_pg_embedding 
                    WHERE collection_id = CAST(:collection_id AS UUID)
                """), {"collection_id": str(row.uuid)})
                
                doc_count = doc_count_result.scalar() or 0
                logger.info(f"Collection {collection_name} ({row.uuid}) has {doc_count} documents")
                
                # Get created_at from collection metadata first, then from documents
                created_at = None
                
                # 1. Try to get from collection metadata
                if isinstance(metadata, dict):
                    created_at = metadata.get("created_at") or metadata.get("created_date")
                
                # 2. If not in metadata, try to get from the oldest document's metadata
                if not created_at and doc_count > 0:
                    try:
                        doc_metadata_result = await session.execute(text("""
                            SELECT cmetadata
                            FROM langchain_pg_embedding 
                            WHERE collection_id = CAST(:collection_id AS UUID)
                            ORDER BY uuid ASC
                            LIMIT 1
                        """), {"collection_id": str(row.uuid)})
                        
                        doc_metadata_row = doc_metadata_result.fetchone()
                        if doc_metadata_row and doc_metadata_row.cmetadata:
                            doc_metadata = doc_metadata_row.cmetadata
                            if isinstance(doc_metadata, str):
                                try:
                                    doc_metadata = json.loads(doc_metadata)
                                except:
                                    doc_metadata = {}
                            
                            if isinstance(doc_metadata, dict):
                                created_at = (
                                    doc_metadata.get("created_at") or 
                                    doc_metadata.get("created_date") or 
                                    doc_metadata.get("upload_date") or
                                    doc_metadata.get("date") or
                                    doc_metadata.get("timestamp")
                                )
                    except Exception as e:
                        logger.debug(f"Failed to get created_at from document metadata: {e}")
                
                # Get sample documents
                sample_docs_result = await session.execute(text("""
                    SELECT 
                        document,
                        cmetadata
                    FROM langchain_pg_embedding 
                    WHERE collection_id = CAST(:collection_id AS UUID)
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
                    "metadata": metadata,
                    "created_at": created_at,
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
            # For shared collections, user_id should be NULL so all users can access it
            # For personal collections, user_id should be set to the creator's user_id
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
                            "is_shared": is_shared,
                            "created_at": datetime.now().isoformat()  # Store creation timestamp
                        }),
                        "user_id": None if is_shared else user_id  # Shared collections have NULL user_id
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
                    text("DELETE FROM langchain_pg_embedding WHERE collection_id = CAST(:collection_id AS UUID)"),
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
                    
                    # Use proper parameterized queries to avoid type casting issues
                    logger.info(f"Executing SQL with is_shared: {is_shared}, created_by: {original_user_id or 'system'}")
                    
                    sql = """
                        UPDATE langchain_pg_collection 
                        SET user_id = NULL,
                            cmetadata = jsonb_set(
                                jsonb_set(COALESCE(cmetadata, '{}'::jsonb), '{is_shared}', :is_shared_value::jsonb),
                                '{created_by}', :created_by_value::jsonb
                            )
                        WHERE name = :collection_name
                    """
                    
                    result = await session.execute(text(sql), {
                        "collection_name": collection_name,
                        "is_shared_value": json.dumps(is_shared),
                        "created_by_value": json.dumps(original_user_id or "system")
                    })
                else:
                    # Use proper parameterized queries to avoid type casting issues
                    sql = """
                        UPDATE langchain_pg_collection 
                        SET user_id = :new_user_id,
                            cmetadata = jsonb_set(COALESCE(cmetadata, '{}'::jsonb), '{is_shared}', :is_shared_value::jsonb)
                        WHERE name = :collection_name
                    """
                    
                    result = await session.execute(text(sql), {
                        "new_user_id": new_user_id, 
                        "collection_name": collection_name,
                        "is_shared_value": json.dumps(is_shared)
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
                use_jsonb=True,  # Use JSONB for metadata to avoid deprecation warning
                pre_delete_collection=False  # Don't delete existing collection
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
