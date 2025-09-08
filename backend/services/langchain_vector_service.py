"""
LangChain-based Vector Store service for PostgreSQL + pgvector
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.documents import Document
from langchain_community.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config.settings import settings
from backend.services.database_service import db_service

logger = logging.getLogger(__name__)

class LangChainVectorService:
    """LangChain-based vector store service using PostgreSQL + pgvector"""
    
    def __init__(self):
        self.documents = None
        self.embeddings = None
        self.text_splitter = None
        
    async def initialize(self):
        """Initialize LangChain vector service"""
        try:
            # Initialize Ollama embeddings
            self.embeddings = OllamaEmbeddings(
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
            connection_string = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
            
            self.documents = PGVector(
                connection_string=connection_string,
                embedding_function=self.embeddings,
                collection_name="documents",
                distance_strategy="cosine"
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
            
            # Create document
            doc = Document(
                page_content=content,
                metadata=metadata or {}
            )
            
            # Split document into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunks to vector store
            doc_ids = await self.documents.aadd_documents(chunks)
            
            logger.info(f"Added {len(doc_ids)} document chunks to vector store")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
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
            docs_with_scores = await self.documents.asimilarity_search_with_score(
                query=query,
                k=top_k
            )
            
            # Filter by similarity threshold and format results
            documents = []
            for doc, score in docs_with_scores:
                # Convert distance to similarity (1 - distance for cosine similarity)
                similarity = 1 - score
                
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
            if not db_service.async_session_factory:
                raise Exception("Database not initialized")
            
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
            if not db_service.async_session_factory:
                raise Exception("Database not initialized")
            
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
    
    async def close(self):
        """Close vector service"""
        try:
            if self.documents:
                # PGVector doesn't have a close method
                pass
            logger.info("LangChain vector service closed")
        except Exception as e:
            logger.error(f"Failed to close vector service: {e}")

# Global LangChain vector service instance
langchain_vector_service = LangChainVectorService()
