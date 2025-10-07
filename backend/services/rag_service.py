"""
RAG (Retrieval-Augmented Generation) service
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
import re

from backend.config.settings import settings
from backend.services.vector_service import vector_service
from backend.services.ollama_service import ollama_service
from backend.services.prompt_service import prompt_service

logger = logging.getLogger(__name__)

class RagService:
    """RAG service for retrieval-augmented generation"""
    
    def __init__(self):
        self.vector_service = vector_service
        self.ollama_service = ollama_service
        
    async def initialize(self):
        """Initialize RAG service"""
        try:
            await self.vector_service.initialize()
            await self.ollama_service.initialize()
            logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None, collection_name: Optional[str] = None) -> str:
        """Add document to knowledge base"""
        try:
            # Clean and preprocess content
            cleaned_content = self._preprocess_content(content)
            
            # Add to vector database
            doc_id = await self.vector_service.add_document(cleaned_content, metadata, collection_name)
            
            logger.info(f"Document added to knowledge base: {doc_id} in collection: {collection_name}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    async def search_context(self, query: str, max_docs: int = None) -> List[Dict[str, Any]]:
        """Search for relevant context using vector similarity"""
        try:
            max_docs = max_docs or settings.RAG_CONTEXT_MAX_DOCS
            
            # Search similar documents using optimized method
            documents = await self.vector_service.search_similar_optimized(
                query=query,
                top_k=settings.RAG_VECTOR_SEARCH_TOP_K,
                similarity_threshold=settings.RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD
            )
            
            # Filter duplicates if enabled
            if settings.RAG_SEARCH_FILTER_DUPLICATES:
                documents = self._filter_duplicates(documents)
            
            # Limit to max_docs
            documents = documents[:max_docs]
            
            # Ensure minimum results
            if len(documents) < settings.RAG_VECTOR_SEARCH_MIN_RESULTS:
                logger.warning(f"Only found {len(documents)} documents, minimum required: {settings.RAG_VECTOR_SEARCH_MIN_RESULTS}")
            
            logger.info(f"Found {len(documents)} relevant documents for query")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search context: {e}")
            # Return empty list to allow fallback to basic chat
            return []
    
    async def generate_response(self, query: str, context: List[Dict[str, Any]] = None, chat_history: List[Dict[str, str]] = None, model_type: str = "fast") -> Dict[str, Any]:
        """Generate response using RAG with enhanced prompting and optimized processing"""
        try:
            # Search context if not provided
            if context is None:
                context = await self.search_context(query)
            
            # Build enhanced prompt using prompt service (optimized)
            enhanced_prompt = prompt_service.build_rag_prompt(query, context)
            
            # Pre-validate prompt length to avoid unnecessary processing (추가 최적화)
            max_prompt_length = settings.OLLAMA_CHAT_NUM_CTX * 3  # 더 엄격한 길이 제한
            if len(enhanced_prompt) > max_prompt_length:
                logger.warning(f"Prompt too long ({len(enhanced_prompt)} chars), truncating context")
                # Truncate context to fit within limits (더 공격적인 축소)
                context = context[:max(1, len(context) // 3)]
                enhanced_prompt = prompt_service.build_rag_prompt(query, context)
            
            # Generate response using the enhanced prompt with optimized settings
            try:
                llm_response = await self.ollama_service.generate(enhanced_prompt, model_type=model_type)
            except Exception as e:
                logger.error(f"Failed to generate RAG response: {e}")
                # Return error response instead of raising exception
                return {
                    "success": False,
                    "error": f"LLM 생성 실패: {str(e)}",
                    "response": None,
                    "context": context,
                    "metadata": {
                        "context_count": len(context) if context else 0,
                        "error_mode": True,
                        "rag_mode": "RAG"
                    }
                }
            
            # Get model info from settings
            model_config = settings.MODEL_CONFIGS.get(model_type, {})
            model_name = model_config.get("model", settings.MODEL_NAME)
            
            # Optimized Korean response validation (reduce false positives)
            if len(llm_response) > 20 and self._is_english_response(llm_response):
                logger.warning("Detected English response in RAG, forcing Korean response")
                llm_response = self._force_korean_response(llm_response, query)
            
            # Format response with metadata including model info
            formatted_response = {
                "response": llm_response,
                "context": context,
                "metadata": {
                    "context_count": len(context),
                    "prompt_length": len(enhanced_prompt),
                    "enhanced_prompting": True
                },
                "model_info": {
                    "model_type": model_type,
                    "model": model_name
                }
            }
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            raise
    
    async def rag_query(self, query: str, session_id: str = None, model_type: str = "fast") -> Dict[str, Any]:
        """Main RAG query method"""
        try:
            # Search for relevant context
            context = await self.search_context(query)
            
            # Check if we have enough context
            if not context and settings.RAG_STRICT_MODE_ENABLED:
                return {
                    "success": False,
                    "error": "No relevant context found and strict mode is enabled",
                    "response": None,
                    "context": [],
                    "metadata": {
                        "context_count": 0,
                        "strict_mode": True
                    }
                }
            
            # If no context found, fallback to basic chat
            if not context:
                logger.info("No context found, falling back to basic chat")
                from backend.services.prompt_service import prompt_service
                enhanced_prompt = prompt_service.build_basic_chat_prompt(query)
                response_text = await self.ollama_service.generate(enhanced_prompt, model_type=model_type)
                
                # Get model info for fallback mode
                model_config = settings.MODEL_CONFIGS.get(model_type, {})
                model_name = model_config.get("model", settings.MODEL_NAME)
                
                return {
                    "success": True,
                    "response": response_text,
                    "context": [],
                    "metadata": {
                        "context_count": 0,
                        "context_files": [],
                        "fallback_mode": True,
                        "enhanced_prompting": True,
                        "rag_mode": "기본 RAG"
                    },
                    "model_info": {
                        "model_type": model_type,
                        "model": model_name
                    }
                }
            
            # Generate response with context
            response = await self.generate_response(query, context, model_type=model_type)
            
            # Add metadata with file information
            context_files = []
            similarity_scores = []
            for doc in context:
                doc_metadata = doc.get("metadata", {})
                filename = doc_metadata.get("filename", doc_metadata.get("file_name", ""))
                if filename:
                    context_files.append(filename)
                
                # Collect similarity scores
                similarity = doc.get("similarity", 0)
                similarity_scores.append(similarity)
            
            # Calculate average similarity score
            avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
            metadata = {
                "context_count": len(context),
                "context_sources": [doc.get("id") for doc in context],
                "context_files": context_files,
                "similarity_scores": similarity_scores,
                "similarity": avg_similarity,  # Average similarity score for the response
                "strict_mode": settings.RAG_STRICT_MODE_ENABLED,
                "fallback_enabled": settings.RAG_FALLBACK_TO_GENERAL_KNOWLEDGE,
                "rag_mode": "기본 RAG"
            }
            
            # Get model info from response or settings
            model_info = response.get("model_info", {})
            if not model_info:
                model_config = settings.MODEL_CONFIGS.get(model_type, {})
                model_name = model_config.get("model", settings.MODEL_NAME)
                model_info = {
                    "model_type": model_type,
                    "model": model_name
                }
            
            return {
                "success": True,
                "response": response["response"],
                "context": context,
                "metadata": metadata,
                "model_info": model_info
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": None,
                "context": [],
                "metadata": {}
            }
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for better vector search"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Remove special characters that might interfere with vector search
        content = re.sub(r'[^\w\s.,!?;:-]', '', content)
        
        return content
    
    def _filter_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter duplicate documents based on content similarity"""
        if not documents:
            return documents
        
        unique_docs = []
        seen_contents = set()
        
        for doc in documents:
            content_hash = hash(doc["content"][:100])  # Use first 100 chars as hash
            if content_hash not in seen_contents:
                unique_docs.append(doc)
                seen_contents.add(content_hash)
        
        return unique_docs
    
    def _build_context_string(self, context: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents"""
        if not context:
            return ""
        
        context_parts = []
        for i, doc in enumerate(context, 1):
            content = doc["content"]
            similarity = doc.get("similarity", 0)
            
            # Truncate content if too long
            max_length = settings.RAG_CONTEXT_MAX_LENGTH
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            context_parts.append(f"[{i}] {content} (similarity: {similarity:.3f})")
        
        return "\n\n".join(context_parts)
    
    def _build_messages(self, query: str, context: str, chat_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Build messages for chat completion"""
        messages = []
        
        # Add system message
        system_message = self._build_system_message()
        messages.append({"role": "system", "content": system_message})
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)
        
        # Add current query with context
        user_message = self._build_user_message(query, context)
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _build_system_message(self) -> str:
        """Build system message for RAG with Korean response enforcement"""
        return settings.KOREAN_SYSTEM_PROMPT + """

📚 **RAG 시스템 지침**:
1. 제공된 컨텍스트를 바탕으로 질문에 정확하게 답변하세요
2. 컨텍스트에 충분한 정보가 없다면 명확히 말씀해 주세요
3. 가능한 경우 컨텍스트의 관련 부분을 인용하세요
4. 간결하면서도 포괄적인 응답을 제공하세요
5. 컨텍스트에 없는 내용에 대해 질문받으면 더 많은 정보가 필요하다고 설명하세요

컨텍스트는 사용자 메시지에서 제공됩니다."""
    
    def _build_user_message(self, query: str, context: str) -> str:
        """Build user message with context in Korean"""
        if context:
            return f"""컨텍스트:
{context}

질문: {query}

제공된 컨텍스트를 바탕으로 질문에 답변해 주세요."""
        else:
            return f"질문: {query}"
    
    def _format_response(self, response: Dict[str, Any], context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format response based on settings"""
        formatted = {
            "content": response["content"],
            "model_info": {
                "model": response.get("model", ""),
                "total_duration": response.get("total_duration", 0),
                "eval_count": response.get("eval_count", 0)
            }
        }
        
        # Add context information if enabled
        if settings.RAG_RESPONSE_FORMAT == "structured":
            formatted["context_info"] = {
                "sources": len(context),
                "similarity_scores": [doc.get("similarity", 0) for doc in context]
            }
        
        return formatted
    
    def _is_english_response(self, text: str) -> bool:
        """Check if the response is primarily in English (optimized)"""
        if not text or len(text.strip()) < 10:
            return False
        
        # Sample first 200 characters for faster processing
        sample_text = text[:200]
        
        # Count Korean characters vs English characters
        korean_chars = sum(1 for char in sample_text if '\uac00' <= char <= '\ud7af')
        english_chars = sum(1 for char in sample_text if char.isalpha() and ord(char) < 128)
        
        # More strict threshold to reduce false positives
        total_chars = korean_chars + english_chars
        if total_chars == 0:
            return False
        
        # Consider English if English chars are more than 70% of total
        return (english_chars / total_chars) > 0.7
    
    def _force_korean_response(self, english_text: str, original_query: str) -> str:
        """Force a Korean response by re-querying with Korean enforcement"""
        try:
            # Create a Korean enforcement prompt
            korean_prompt = f"""다음 영어 응답을 한국어로 번역하고, 한국어로 다시 답변해 주세요.

원래 질문: {original_query}

영어 응답:
{english_text}

🚨 **중요**: 반드시 한국어로만 답변하세요. 영어나 다른 언어 사용 금지!

한국어 답변:"""
            
            # Use the LLM directly to get Korean response
            import asyncio
            import concurrent.futures
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, use ThreadPoolExecutor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run, 
                            self.ollama_service.generate(korean_prompt)
                        )
                        korean_response = future.result()
                else:
                    korean_response = loop.run_until_complete(
                        self.ollama_service.generate(korean_prompt)
                    )
            except RuntimeError:
                # No event loop running, safe to use asyncio.run
                korean_response = asyncio.run(
                    self.ollama_service.generate(korean_prompt)
                )
            
            return korean_response
            
        except Exception as e:
            logger.error(f"Failed to force Korean response: {e}")
            # Fallback: return a simple Korean message
            return f"죄송합니다. 질문에 대한 답변을 한국어로 제공하려고 했지만 오류가 발생했습니다. 원래 질문: {original_query}"
    
    async def get_available_collections(self) -> List[Dict[str, Any]]:
        """Get list of available collections from documents table"""
        try:
            return await self.vector_service.get_collections()
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []
    
    async def close(self):
        """Close RAG service"""
        await self.vector_service.close()
        await self.ollama_service.close()
        logger.info("RAG service closed")

# Global RAG service instance
rag_service = RagService()
