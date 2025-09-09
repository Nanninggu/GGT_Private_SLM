"""
LangChain-based RAG (Retrieval-Augmented Generation) service
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain

from config.settings import settings
from services.langchain_vector_service import langchain_vector_service
from services.prompt_service import prompt_service

logger = logging.getLogger(__name__)

class LangChainRagService:
    """LangChain-based RAG service with conversation memory"""
    
    def __init__(self):
        self.llm = None
        self.documents = None
        self.memory = None
        self.qa_chain = None
        self.current_collection = "documents"  # Default collection
        
    async def initialize(self):
        """Initialize LangChain RAG service"""
        try:
            # Initialize Ollama LLM
            self.llm = ChatOllama(
                model=settings.MODEL_NAME,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=settings.OLLAMA_CHAT_TEMPERATURE,
                top_p=settings.OLLAMA_CHAT_TOP_P,
                top_k=settings.OLLAMA_CHAT_TOP_K,
                repeat_penalty=settings.OLLAMA_CHAT_REPEAT_PENALTY,
                num_predict=settings.OLLAMA_CHAT_NUM_PREDICT
            )
            
            # Initialize vector store
            await langchain_vector_service.initialize()
            self.documents = langchain_vector_service.documents
            
            # Initialize conversation memory
            self.memory = ConversationBufferWindowMemory(
                k=settings.RAG_MEMORY_WINDOW_SIZE,
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            
            # Create conversational retrieval chain
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.documents.as_retriever(
                    search_kwargs={
                        "k": settings.RAG_VECTOR_SEARCH_TOP_K,
                        "score_threshold": settings.RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD
                    }
                ),
                memory=self.memory,
                return_source_documents=True,
                verbose=True
            )
            
            logger.info("LangChain RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain RAG service: {e}")
            raise
    
    async def set_collection(self, collection_name: str) -> bool:
        """Change the active collection for RAG queries"""
        try:
            # Check if collection exists
            collections = await self.get_available_collections()
            collection_exists = any(c["name"] == collection_name for c in collections)
            
            if not collection_exists:
                logger.error(f"Collection '{collection_name}' does not exist")
                return False
            
            # Initialize vector store with new collection
            connection_string = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
            
            self.documents = PGVector(
                connection_string=connection_string,
                embedding_function=self.embeddings,
                collection_name=collection_name,
                distance_strategy="cosine"
            )
            
            self.current_collection = collection_name
            
            # Recreate QA chain with new collection
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.documents.as_retriever(
                    search_kwargs={
                        "k": settings.RAG_VECTOR_SEARCH_TOP_K,
                        "score_threshold": settings.RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD
                    }
                ),
                memory=self.memory,
                return_source_documents=True,
                verbose=True
            )
            
            logger.info(f"Switched to collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set collection '{collection_name}': {e}")
            return False
    
    async def get_available_collections(self) -> List[Dict[str, Any]]:
        """Get list of available collections"""
        try:
            return await langchain_vector_service.get_collections()
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection"""
        try:
            return await langchain_vector_service.get_collection_info(collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    async def create_collection(self, collection_name: str, description: str = "") -> Dict[str, Any]:
        """Create a new collection"""
        try:
            return await langchain_vector_service.create_collection(collection_name, description)
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    async def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection and all its documents"""
        try:
            result = await langchain_vector_service.delete_collection(collection_name)
            
            # If we're deleting the current collection, switch to default
            if self.current_collection == collection_name:
                await self.set_collection("documents")
                logger.info(f"Switched to default collection after deleting {collection_name}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise
    
    async def rename_collection(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a collection"""
        try:
            result = await langchain_vector_service.rename_collection(old_name, new_name)
            
            # If we're renaming the current collection, update the current collection
            if self.current_collection == old_name:
                self.current_collection = new_name
                logger.info(f"Updated current collection to {new_name}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to rename collection: {e}")
            raise
    
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add document to knowledge base"""
        try:
            # Clean and preprocess content
            cleaned_content = self._preprocess_content(content)
            
            # Add to vector store
            doc_ids = await langchain_vector_service.add_document(cleaned_content, metadata)
            
            logger.info(f"Document added to knowledge base: {len(doc_ids)} chunks")
            return f"Added {len(doc_ids)} document chunks"
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    async def rag_query(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Main RAG query method using LangChain"""
        try:
            # Use LangChain conversational retrieval chain
            result = await self.qa_chain.ainvoke({"question": query})
            
            # Extract response and source documents
            response_text = result.get("answer", "")
            source_docs = result.get("source_documents", [])
            
            # Format context documents with detailed source information
            context_docs = []
            for i, doc in enumerate(source_docs):
                # Extract source information
                source_info = {
                    "id": doc.metadata.get("id", f"doc_{i}"),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": 1.0,  # LangChain doesn't provide similarity scores directly
                    "source_type": "vector_db",
                    "collection": self.current_collection,
                    "filename": doc.metadata.get("filename", "Unknown"),
                    "page_number": doc.metadata.get("page", 1),
                    "chunk_index": doc.metadata.get("chunk_index", i),
                    "source_url": doc.metadata.get("source_url", ""),
                    "upload_date": doc.metadata.get("upload_date", ""),
                    "file_size": doc.metadata.get("file_size", 0)
                }
                context_docs.append(source_info)
            
            # Add metadata with source information
            metadata = {
                "context_count": len(context_docs),
                "context_sources": [doc.get("id") for doc in context_docs],
                "context_files": [doc.get("filename", "Unknown") for doc in context_docs],
                "similarity_scores": [doc.get("similarity", 0) for doc in context_docs],
                "langchain_mode": True,
                "memory_enabled": True,
                "source_collection": self.current_collection,
                "has_sources": len(context_docs) > 0
            }
            
            # Format response with source information
            formatted_response = response_text
            
            # Add source information to response if sources exist
            if context_docs:
                source_info = "\n\n📚 **참조 출처:**\n"
                for i, doc in enumerate(context_docs, 1):
                    filename = doc.get("filename", "Unknown")
                    page = doc.get("page_number", 1)
                    collection = doc.get("collection", "documents")
                    source_info += f"{i}. **{filename}** (페이지 {page}, 컬렉션: {collection})\n"
                
                formatted_response += source_info
            
            return {
                "success": True,
                "response": formatted_response,
                "context": context_docs,
                "metadata": metadata,
                "model_info": {
                    "model": settings.MODEL_NAME,
                    "langchain": True
                }
            }
            
        except Exception as e:
            logger.error(f"LangChain RAG query failed: {e}")
            return {
                "success": False,
                "error": f"LangChain RAG query failed: {e}",
                "response": None,
                "context": [],
                "metadata": {
                    "context_count": 0,
                    "context_files": [],
                    "error_mode": True,
                    "langchain_mode": True
                }
            }
    
    async def search_context(self, query: str, max_docs: int = None) -> List[Dict[str, Any]]:
        """Search for relevant context using LangChain"""
        try:
            max_docs = max_docs or settings.RAG_CONTEXT_MAX_DOCS
            
            # Search similar documents
            documents = await langchain_vector_service.search_similar(
                query=query,
                top_k=settings.RAG_VECTOR_SEARCH_TOP_K,
                similarity_threshold=settings.RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD
            )
            
            # Limit to max_docs
            documents = documents[:max_docs]
            
            logger.info(f"Found {len(documents)} relevant documents for query")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search context: {e}")
            return []
    
    async def clear_memory(self, session_id: str = None) -> bool:
        """Clear conversation memory"""
        try:
            if self.memory:
                self.memory.clear()
                logger.info("Conversation memory cleared")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
    
    async def get_memory_state(self) -> Dict[str, Any]:
        """Get current memory state"""
        try:
            if self.memory:
                memory_vars = self.memory.load_memory_variables({})
                return {
                    "memory_type": "ConversationBufferWindowMemory",
                    "window_size": settings.RAG_MEMORY_WINDOW_SIZE,
                    "current_messages": len(memory_vars.get("chat_history", [])),
                    "memory_variables": list(memory_vars.keys())
                }
            return {"memory_type": "None", "current_messages": 0}
        except Exception as e:
            logger.error(f"Failed to get memory state: {e}")
            return {"error": str(e)}
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content before adding to vector store"""
        # Remove extra whitespace
        content = " ".join(content.split())
        
        # Remove special characters that might cause issues
        content = content.replace("\x00", "").replace("\r", "")
        
        return content
    
    async def close(self):
        """Close RAG service"""
        try:
            await langchain_vector_service.close()
            logger.info("LangChain RAG service closed")
        except Exception as e:
            logger.error(f"Failed to close RAG service: {e}")
    
    # Collection Management Methods
    async def get_collections(self) -> List[Dict[str, Any]]:
        """Get list of available collections"""
        try:
            return await langchain_vector_service.get_collections()
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific collection"""
        try:
            logger.info(f"Getting collection info for: {collection_name}")
            result = await langchain_vector_service.get_collection_info(collection_name)
            logger.info(f"Collection info result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

# Global LangChain RAG service instance
langchain_rag_service = LangChainRagService()
