"""
Chat service layer for business logic
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.models.chat import ChatSession, ChatMessage, MessageRole, ModelResponse
from backend.repositories.chat_repository import ChatRepository
from backend.services.llm_service import ExaoneLLMService
from backend.services.rag_service import rag_service
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class ChatService:
    """Service layer for chat functionality"""

    def __init__(self):
        self.repository = ChatRepository()
        self.llm_service = ExaoneLLMService()
        self.rag_service = rag_service
        self._initialized = False

    def create_session(self) -> ChatSession:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        session = ChatSession(
            id=session_id,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.repository.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get existing chat session"""
        return self.repository.load_session(session_id)

    async def initialize(self):
        """Initialize RAG service"""
        if not self._initialized:
            try:
                await self.rag_service.initialize()
                self._initialized = True
                logger.info("ChatService initialized with RAG")
            except Exception as e:
                logger.error(f"Failed to initialize RAG service: {e}")
                raise

    async def send_message(self, session_id: str, user_message: str) -> tuple[ChatMessage, ChatMessage]:
        """Send a message and get AI response using RAG"""
        # Initialize RAG service if not already done
        if not self._initialized:
            await self.initialize()

        # Load or create session
        session = self.get_session(session_id)
        if not session:
            session = self.create_session()
            session.id = session_id

        # Create user message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.now(),
            session_id=session_id
        )

        # Add user message to session
        session.add_message(user_msg)

        # Get recent messages for context (limit to MAX_HISTORY)
        recent_messages = session.messages[-settings.MAX_HISTORY:]

        try:
            # Use RAG service to generate response
            logger.info(f"Processing RAG query: {user_message[:100]}...")
            rag_result = await self.rag_service.rag_query(user_message, session_id)
            
            if rag_result["success"]:
                # RAG-based response
                response_content = rag_result["response"]
                context_count = rag_result["metadata"].get("context_count", 0)
                context_files = rag_result["metadata"].get("context_files", [])
                
                logger.info(f"RAG response generated with {context_count} context documents")
                if context_files:
                    logger.info(f"Context files: {context_files}")
            else:
                # Fallback to basic LLM response
                logger.warning("RAG failed, falling back to basic LLM response")
                model_response = self.llm_service.generate_response(recent_messages)
                response_content = model_response.content
                
        except Exception as e:
            logger.error(f"RAG processing failed: {e}, falling back to basic LLM")
            # Fallback to basic LLM response
            model_response = self.llm_service.generate_response(recent_messages)
            response_content = model_response.content

        # Create assistant message
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=response_content,
            timestamp=datetime.now(),
            session_id=session_id
        )

        # Add assistant message to session
        session.add_message(assistant_msg)

        # Save session
        self.repository.save_session(session)

        return user_msg, assistant_msg

    def get_chat_history(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get chat history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []

        messages = session.messages
        if limit:
            messages = messages[-limit:]

        return messages

    def get_all_sessions(self) -> List[str]:
        """Get all session IDs"""
        return self.repository.get_all_sessions()

    def clear_session(self, session_id: str) -> bool:
        """Clear a chat session"""
        session = self.get_session(session_id)
        if session:
            session.messages = []
            session.updated_at = datetime.now()
            return self.repository.save_session(session)
        return False
