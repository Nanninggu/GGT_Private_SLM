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
# from langchain.memory import ConversationBufferWindowMemory
# from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import PGVector

from config.settings import settings
from services.langchain_vector_service import langchain_vector_service
from services.prompt_service import prompt_service

logger = logging.getLogger(__name__)

class LangChainRagService:
    """LangChain-based RAG service with conversation memory"""
    
    def __init__(self):
        self.llm = None
        self.documents = None
        self.embeddings = None
        self.current_collection = "langchain_documents"  # Default collection
        
    async def initialize(self):
        """Initialize LangChain RAG service"""
        try:
            # Initialize Ollama LLM with Korean response enforcement
            self.llm = ChatOllama(
                model=settings.MODEL_NAME,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=settings.OLLAMA_CHAT_TEMPERATURE,
                top_p=settings.OLLAMA_CHAT_TOP_P,
                top_k=settings.OLLAMA_CHAT_TOP_K,
                repeat_penalty=settings.OLLAMA_CHAT_REPEAT_PENALTY,
                num_predict=settings.OLLAMA_CHAT_NUM_PREDICT,
                # Add system message for Korean response enforcement
                system=settings.KOREAN_SYSTEM_PROMPT
            )
            
            # Initialize vector store
            await langchain_vector_service.initialize()
            self.documents = langchain_vector_service.documents
            self.embeddings = langchain_vector_service.embeddings
            
            # Initialize simple RAG without memory for now
            logger.info("LangChain RAG service initialized (simplified version without memory)")
            
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
            
            # Update the vector service to use the new collection
            await langchain_vector_service.set_collection(collection_name)
            
            # Update our documents reference
            self.documents = langchain_vector_service.documents
            self.current_collection = collection_name
            
            # Update documents reference for new collection
            logger.info(f"Updated documents reference for collection: {collection_name}")
            
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
                await self.set_collection("langchain_documents")
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
            logger.info(f"Starting document addition to knowledge base: {len(content)} characters")
            
            # Clean and preprocess content
            logger.info("Preprocessing content...")
            cleaned_content = self._preprocess_content(content)
            logger.info(f"Content preprocessed: {len(cleaned_content)} characters")
            
            # Add to vector store
            logger.info("Adding document to vector store...")
            doc_ids = await langchain_vector_service.add_document(cleaned_content, metadata)
            
            logger.info(f"Document successfully added to knowledge base: {len(doc_ids)} chunks")
            return f"Added {len(doc_ids)} document chunks"
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    def _is_english_response(self, text: str) -> bool:
        """Check if the response is primarily in English"""
        if not text or len(text.strip()) < 10:
            return False
        
        # Count Korean characters vs English characters
        korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        
        # If there are more English characters than Korean, consider it English
        return english_chars > korean_chars
    
    async def _force_korean_response_async(self, english_text: str, original_query: str) -> str:
        """Force a Korean response by re-querying with Korean enforcement (async version)"""
        try:
            # Create a Korean enforcement prompt
            korean_prompt = f"""다음 영어 응답을 한국어로 번역하고, 한국어로 다시 답변해 주세요.

원래 질문: {original_query}

영어 응답:
{english_text}

🚨 **중요**: 반드시 한국어로만 답변하세요. 영어나 다른 언어 사용 금지!

한국어 답변:"""
            
            # Use the LLM directly to get Korean response
            korean_response = await self.llm.ainvoke([{"role": "user", "content": korean_prompt}])
            return korean_response.content if hasattr(korean_response, 'content') else str(korean_response)
            
        except Exception as e:
            logger.error(f"Failed to force Korean response: {e}")
            # Fallback: return a simple Korean message
            return f"죄송합니다. 질문에 대한 답변을 한국어로 제공하려고 했지만 오류가 발생했습니다. 원래 질문: {original_query}"
    
    def _force_korean_response(self, english_text: str, original_query: str) -> str:
        """Force a Korean response by re-querying with Korean enforcement (sync wrapper)"""
        try:
            # Use asyncio.run to handle the async call
            import asyncio
            return asyncio.run(self._force_korean_response_async(english_text, original_query))
        except Exception as e:
            logger.error(f"Failed to force Korean response: {e}")
            # Fallback: return a simple Korean message
            return f"죄송합니다. 질문에 대한 답변을 한국어로 제공하려고 했지만 오류가 발생했습니다. 원래 질문: {original_query}"
    
    async def rag_query(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Main RAG query method using LangChain"""
        try:
            # Search for relevant documents
            source_docs = await self.documents.asimilarity_search(
                query,
                k=settings.RAG_VECTOR_SEARCH_TOP_K,
                score_threshold=settings.RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD
            )
            
            # Create context from source documents
            context = "\n\n".join([doc.page_content for doc in source_docs])
            
            # Create prompt for LLM
            prompt = f"""다음 컨텍스트를 바탕으로 질문에 답변해 주세요. 컨텍스트에서 답을 찾을 수 없다면 "죄송합니다. 제공된 컨텍스트에서 해당 질문에 대한 답변을 찾을 수 없습니다."라고 답변해 주세요.

컨텍스트:
{context}

질문: {query}

답변:"""
            
            # Get response from LLM
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Force Korean response if the response is in English
            if self._is_english_response(response_text):
                logger.warning("Detected English response, forcing Korean response")
                response_text = await self._force_korean_response_async(response_text, query)
            
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
            
            # Calculate average similarity score
            similarity_scores = [doc.get("similarity", 0) for doc in context_docs]
            avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
            # Add metadata with source information
            metadata = {
                "context_count": len(context_docs),
                "context_sources": [doc.get("id") for doc in context_docs],
                "context_files": [doc.get("filename", "Unknown") for doc in context_docs],
                "similarity_scores": similarity_scores,
                "similarity": avg_similarity,  # Average similarity score for the response
                "langchain_mode": True,
                "memory_enabled": True,
                "source_collection": self.current_collection,
                "has_sources": len(context_docs) > 0
            }
            
            # Format response without source information
            formatted_response = response_text
            
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
        """Clear conversation memory (simplified - no memory in current implementation)"""
        try:
            logger.info("Memory clear requested (no memory in current implementation)")
            return True
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
    
    async def get_memory_state(self) -> Dict[str, Any]:
        """Get current memory state (simplified - no memory in current implementation)"""
        try:
            return {
                "memory_type": "None",
                "current_messages": 0,
                "note": "Memory disabled in current implementation"
            }
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
