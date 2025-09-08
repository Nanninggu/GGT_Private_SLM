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

from backend.config.settings import settings
from backend.services.langchain_vector_service import langchain_vector_service
from backend.services.prompt_service import prompt_service

logger = logging.getLogger(__name__)

class LangChainRagService:
    """LangChain-based RAG service with conversation memory"""
    
    def __init__(self):
        self.llm = None
        self.documents = None
        self.memory = None
        self.qa_chain = None
        
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
            
            # Format context documents
            context_docs = []
            for doc in source_docs:
                context_docs.append({
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity": 1.0  # LangChain doesn't provide similarity scores directly
                })
            
            # Add metadata
            metadata = {
                "context_count": len(context_docs),
                "context_sources": [doc.get("id") for doc in context_docs],
                "context_files": [doc.get("metadata", {}).get("filename", "") for doc in context_docs],
                "similarity_scores": [doc.get("similarity", 0) for doc in context_docs],
                "langchain_mode": True,
                "memory_enabled": True
            }
            
            return {
                "success": True,
                "response": response_text,
                "context": context_docs,
                "metadata": metadata,
                "model_info": {
                    "model": settings.MODEL_NAME,
                    "langchain": True
                }
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            
            # Fallback to basic chat
            try:
                logger.info("Falling back to basic chat")
                enhanced_prompt = prompt_service.build_basic_chat_prompt(query)
                
                # Use LangChain LLM for fallback
                response = await self.llm.ainvoke(enhanced_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                return {
                    "success": True,
                    "response": response_text,
                    "context": [],
                    "metadata": {
                        "context_count": 0,
                        "context_files": [],
                        "fallback_mode": True,
                        "langchain_mode": True,
                        "enhanced_prompting": True
                    },
                    "model_info": {
                        "model": settings.MODEL_NAME,
                        "langchain": True
                    }
                }
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return {
                    "success": False,
                    "error": f"RAG query failed: {e}. Fallback also failed: {fallback_error}",
                    "response": None,
                    "context": [],
                    "metadata": {
                        "context_count": 0,
                        "context_files": [],
                        "error_mode": True
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

# Global LangChain RAG service instance
langchain_rag_service = LangChainRagService()
