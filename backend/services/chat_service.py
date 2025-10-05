"""
Chat service layer for business logic
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from backend.models.chat import ChatSession, ChatMessage, MessageRole, ModelResponse, SourceInfo, AccuracyInfo
from backend.repositories.db_chat_repository import DBChatRepository
from backend.services.ollama_service import ollama_service
from backend.services.langchain_rag_service import langchain_rag_service
from backend.services.quality_service import quality_service
from backend.services.personalization_service import personalization_service
from backend.services.monitoring_service import get_monitoring_service
from backend.config.settings import settings

logger = logging.getLogger(__name__)

class ChatService:
    """Service layer for chat functionality"""

    """
        # `self`는 해당 클래스의 인스턴스 자체를 가리킴.
        # 인스턴스 메서드에서 인스턴스 속성과 다른 메서드에 접근/수정할 때 사용됨.
        # 각 인스턴스는 별도의 `self.*` 속성 집합을 가짐.
        # 결국 외부 코드를 self.* 을 통해 해당 코드를 사용 할 수 있게 됨. (ex. self.repository = DBChatRepository())
    """
    def __init__(self):
        self.repository = DBChatRepository()    # 인스턴스별 DB 리포지토리 할당
        self.llm_service = ollama_service   # 외부 LLM 서비스 참조 할당
        self.rag_service = langchain_rag_service    # RAG 서비스 참조 할당
        self._initialized = False   # 인스턴스 초기화 상태 플래그


    """
    Create a new chat session

    예제:
    입력값:
      - 없음 (메서드 호출 시 self는 ChatService 인스턴스)

    출력값(리턴):
      - ChatSession 객체

    예시 리턴값(의사표현, 실제 타입은 ChatSession):
    ChatSession(
        id='550e8400-e29b-41d4-a716-446655440000',
        messages=[],  # List[ChatMessage], 새 세션은 빈 리스트
        created_at=datetime(2025, 10, 5, 10, 0, 0),
        updated_at=datetime(2025, 10, 5, 10, 0, 0)
    )

    dict 형태(디버깅/로그용 예시):
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "messages": [],
        "created_at": "2025-10-05T10:00:00",
        "updated_at": "2025-10-05T10:00:00"
        
        추가로 리턴 타입은 ChatSession 객체임.
        함수 시그니처가 async def create_session(self) -> ChatSession:로 되어 있어 타입 힌트는 ChatSession이고, 
        정상 종료 시 ChatSession 객체를 반환합니다. 
        비동기 함수이므로 호출자는 await로 결과를 받아야 하며, 예외 발생 시 예외가 전파됩니다.
    }
    """
    async def create_session(self) -> ChatSession:
        """Create a new chat session"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Creating new session in ChatService...")
            
            session_id = str(uuid.uuid4())
            logger.info(f"Generated session ID: {session_id}")
            
            session = ChatSession(
                id=session_id,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            logger.info("ChatSession object created")
            
            success = await self.repository.save_session(session)
            logger.info(f"Session save result: {success}")
            
            return session
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in create_session: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get existing chat session"""
        return await self.repository.load_session(session_id)
    
    async def save_session(self, session: ChatSession) -> bool:
        """Save a chat session"""
        return await self.repository.save_session(session)

    async def initialize(self):
        """Initialize RAG service and database repository"""
        if not self._initialized:
            try:
                await self.repository.initialize()
                await self.rag_service.initialize()
                self._initialized = True
                logger.info("ChatService initialized with RAG and database")
            except Exception as e:
                logger.error(f"Failed to initialize ChatService: {e}")
                raise

    async def send_message(self, session_id: str, user_message: str, model_type: str = "fast", user_id: str = "default") -> tuple[ChatMessage, ChatMessage]:
        """Send a message and get AI response using RAG with personalization"""
        # Initialize RAG service if not already done
        if not self._initialized:
            await self.initialize()

        # Load or create session
        session = await self.get_session(session_id)
        if not session:
            session = await self.create_session()
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

        # Initialize response variables
        response_content = ""
        sources = []
        accuracy_info = None
        
        try:
            # Apply personalization to the query
            personalized_query = personalization_service.customize_prompt(
                user_message, user_id, user_message
            )
            
            # Use LangChain RAG service to generate response
            logger.info(f"Processing personalized LangChain RAG query with model type {model_type}: {user_message[:100]}...")
            rag_result = await self.rag_service.rag_query(personalized_query, session_id, model_type)
            
            if rag_result["success"]:
                # RAG-based response
                response_content = rag_result["response"]
                context_count = rag_result["metadata"].get("context_count", 0)
                context_files = rag_result["metadata"].get("context_files", [])
                similarity_scores = rag_result["metadata"].get("similarity_scores", [])
                avg_similarity = rag_result["metadata"].get("similarity", 0.0)
                fallback_used = rag_result["metadata"].get("fallback_mode", False)
                
                # Extract source information
                if rag_result.get("context"):
                    for i, doc in enumerate(rag_result["context"]):
                        doc_metadata = doc.get("metadata", {})
                        filename = doc_metadata.get("filename", doc_metadata.get("file_name", f"Document {i+1}"))
                        similarity = doc.get("similarity", 0.0)
                        content_preview = doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
                        document_id = doc.get("id", f"doc_{i}")
                        
                        sources.append(SourceInfo(
                            filename=filename,
                            similarity_score=similarity,
                            content_preview=content_preview,
                            document_id=document_id
                        ))
                
                # Apply personalization to response format
                response_content = personalization_service.customize_response_format(
                    response_content, user_id
                )
                
                # Assess response quality
                quality_metrics = quality_service.assess_response_quality(
                    user_question=user_message,
                    response=response_content,
                    context_documents=rag_result.get("context", []),
                    sources=sources
                )
                
                # Create enhanced accuracy information with quality metrics
                accuracy_info = AccuracyInfo(
                    confidence_score=avg_similarity,
                    context_count=context_count,
                    avg_similarity=avg_similarity,
                    fallback_used=fallback_used
                )
                
                logger.info(f"LangChain RAG response generated with {context_count} context documents")
                if context_files:
                    logger.info(f"Context files: {context_files}")
            else:
                # If RAG fails, return error message instead of fallback
                logger.error(f"LangChain RAG failed: {rag_result.get('error', 'Unknown error')}")
                response_content = f"죄송합니다. 현재 vector DB에서 관련 정보를 찾을 수 없어 답변을 생성할 수 없습니다. 먼저 관련 문서를 업로드해 주세요. 오류: {rag_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            logger.error(f"LangChain RAG processing failed: {e}")
            response_content = f"죄송합니다. RAG 시스템에 오류가 발생했습니다. 먼저 관련 문서를 업로드해 주세요. 오류: {str(e)}"

        # Get model info from RAG result
        model_info = rag_result.get("model_info", {}) if rag_result.get("success") else {}
        model_name = model_info.get("model", "exaone3.5:2.4b")
        
        # Create assistant message with source, accuracy, and quality information
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=response_content,
            timestamp=datetime.now(),
            session_id=session_id,
            sources=sources,
            accuracy=accuracy_info,
            metadata={
                "model_type": model_type,
                "model_name": model_name,
                "rag_mode": "LangChain RAG",
                "model_info": model_info,
                "quality_metrics": {
                    "overall_score": quality_metrics.overall_score,
                    "completeness_score": quality_metrics.completeness_score,
                    "accuracy_score": quality_metrics.accuracy_score,
                    "relevance_score": quality_metrics.relevance_score,
                    "clarity_score": quality_metrics.clarity_score,
                    "structure_score": quality_metrics.structure_score,
                    "quality_level": quality_service.get_quality_level(quality_metrics.overall_score),
                    "issues": quality_metrics.issues,
                    "suggestions": quality_metrics.suggestions
                } if 'quality_metrics' in locals() else {}
            }
        )

        # Add assistant message to session
        session.add_message(assistant_msg)

        # Record metrics for monitoring
        response_time = (assistant_msg.timestamp - user_msg.timestamp).total_seconds()
        quality_score = quality_metrics.overall_score if 'quality_metrics' in locals() else 0.5
        user_satisfaction = 0.5  # Default, would be updated based on feedback
        
        # Get monitoring service and record metrics
        monitoring_svc = get_monitoring_service()
        monitoring_svc.record_metrics(
            response_time=response_time,
            quality_score=quality_score,
            user_satisfaction=user_satisfaction,
            error_occurred=not rag_result.get("success", False),
            active_users=1
        )

        # Save session
        await self.repository.save_session(session)

        return user_msg, assistant_msg

    async def get_chat_history(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get chat history for a session"""
        session = await self.get_session(session_id)
        if not session:
            return []

        messages = session.messages
        if limit:
            messages = messages[-limit:]

        return messages

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs"""
        return await self.repository.get_all_sessions()

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists without loading all sessions"""
        return await self.repository.session_exists(session_id)

    async def clear_session(self, session_id: str) -> bool:
        """Clear a chat session"""
        return await self.repository.clear_session(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session completely"""
        return await self.repository.delete_session(session_id)

    async def clear_all_sessions(self) -> List[str]:
        """Clear all sessions except default"""
        return await self.repository.clear_all_sessions()
    
    # Database-based session management methods
    async def create_chat_session(self, session_id: str, user_id: str, title: str) -> Dict[str, Any]:
        """Create a new chat session in database"""
        try:
            # Use the database function to create/update session
            result = await self.repository.execute_query(
                "SELECT update_session_title(%s, %s, %s)",
                (session_id, title, user_id)
            )
            
            if result and result[0][0]:  # Function returned True
                return {
                    "session_id": session_id,
                    "user_id": user_id,
                    "title": title,
                    "created_at": datetime.now().isoformat()
                }
            else:
                raise Exception("Failed to create session")
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise e
    
    async def update_session_title(self, session_id: str, title: str, user_id: str = "default") -> bool:
        """Update chat session title in database"""
        try:
            result = await self.repository.execute_query(
                "SELECT update_session_title(%s, %s, %s)",
                (session_id, title, user_id)
            )
            return result and result[0][0] if result else False
        except Exception as e:
            logger.error(f"Error updating session title: {e}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        try:
            result = await self.repository.execute_query(
                """
                SELECT session_id, title, title_edited, created_at, updated_at, 
                       last_activity, message_count, is_active
                FROM user_active_sessions 
                WHERE user_id = %s
                ORDER BY last_activity DESC
                """,
                (user_id,)
            )
            
            sessions = []
            for row in result:
                sessions.append({
                    "session_id": row[0],
                    "title": row[1],
                    "title_edited": row[2],
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None,
                    "last_activity": row[5].isoformat() if row[5] else None,
                    "message_count": row[6],
                    "is_active": row[7]
                })
            
            return sessions
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        try:
            result = await self.repository.execute_query(
                """
                SELECT session_id, user_id, title, title_edited, created_at, 
                       updated_at, last_activity, message_count, is_active
                FROM chat_sessions 
                WHERE session_id = %s
                """,
                (session_id,)
            )
            
            if result:
                row = result[0]
                return {
                    "session_id": row[0],
                    "user_id": row[1],
                    "title": row[2],
                    "title_edited": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                    "updated_at": row[5].isoformat() if row[5] else None,
                    "last_activity": row[6].isoformat() if row[6] else None,
                    "message_count": row[7],
                    "is_active": row[8]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    async def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session from database"""
        try:
            result = await self.repository.execute_query(
                "SELECT deactivate_session(%s)",
                (session_id,)
            )
            return result and result[0][0] if result else False
        except Exception as e:
            logger.error(f"Error deleting chat session: {e}")
            return False
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update session activity and message count"""
        try:
            result = await self.repository.execute_query(
                "SELECT update_session_message_count(%s)",
                (session_id,)
            )
            return result and result[0][0] if result else False
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            return False

    async def get_session_stats(self, session_id: str) -> dict:
        """Get session statistics"""
        return await self.repository.get_session_stats(session_id)
