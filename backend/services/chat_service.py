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
from backend.utils.helpers import generate_session_id

logger = logging.getLogger(__name__)

class ChatService:
    """Service layer for chat functionality"""

    def __init__(self):
        self.repository = DBChatRepository()
        self.llm_service = ollama_service
        self.rag_service = langchain_rag_service
        self._initialized = False

    async def create_session(self, user_id: str = "default") -> ChatSession:
        """Create a new chat session"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Creating new session in ChatService...")
            
            session_id = generate_session_id(user_id)
            logger.info(f"Generated session ID: {session_id}")
            
            session = ChatSession(
                id=session_id,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=user_id
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

    async def get_all_sessions(self, current_user: Optional[Any] = None) -> List[str]:
        """Get all session IDs"""
        user_id = None
        if current_user and current_user.role.value != 'admin':
            user_id = current_user.id
        return await self.repository.get_all_sessions(user_id)

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
            # Check if session exists
            check_result = await self.repository.execute_query(
                "SELECT session_id FROM chat_sessions WHERE session_id = %s",
                (session_id,)
            )
            
            if check_result:
                # Update existing session
                await self.repository.execute_query(
                    """
                    UPDATE chat_sessions 
                    SET 
                        title = %s,
                        title_edited = TRUE,
                        updated_at = CURRENT_TIMESTAMP,
                        last_activity = CURRENT_TIMESTAMP,
                        user_id = COALESCE(%s, user_id)
                    WHERE session_id = %s
                    """,
                    (title, user_id, session_id)
                )
            else:
                # Create new session if it doesn't exist
                await self.repository.execute_query(
                    """
                    INSERT INTO chat_sessions (session_id, user_id, title, title_edited, created_at, updated_at, last_activity)
                    VALUES (%s, %s, %s, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (session_id, user_id, title)
                )
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "title": title,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise e
    
    async def update_session_title(self, session_id: str, title: str, user_id: str = "default") -> bool:
        """Update chat session title in database"""
        try:
            # Check if session exists
            check_result = await self.repository.execute_query(
                "SELECT session_id FROM chat_sessions WHERE session_id = %s",
                (session_id,)
            )
            
            if check_result:
                # Update existing session
                await self.repository.execute_query(
                    """
                    UPDATE chat_sessions 
                    SET 
                        title = %s,
                        title_edited = TRUE,
                        updated_at = CURRENT_TIMESTAMP,
                        last_activity = CURRENT_TIMESTAMP,
                        user_id = COALESCE(%s, user_id)
                    WHERE session_id = %s
                    """,
                    (title, user_id, session_id)
                )
            else:
                # Create new session if it doesn't exist
                await self.repository.execute_query(
                    """
                    INSERT INTO chat_sessions (session_id, user_id, title, title_edited, created_at, updated_at, last_activity)
                    VALUES (%s, %s, %s, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (session_id, user_id, title)
                )
            return True
        except Exception as e:
            logger.error(f"Error updating session title: {e}")
            return False
    
    async def update_session_description(self, session_id: str, description: str, user_id: str = "default") -> bool:
        """Update chat session description in database"""
        try:
            # Ensure description column exists
            try:
                await self.repository.execute_query(
                    "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS description TEXT DEFAULT NULL"
                )
                logger.info("Added description column to chat_sessions table")
            except Exception as e:
                logger.warning(f"Could not add description column: {e}")

            # Check if session exists
            check_result = await self.repository.execute_query(
                "SELECT session_id FROM chat_sessions WHERE session_id = %s",
                (session_id,)
            )

            if check_result and len(check_result) > 0:
                # Update existing session - only update description and updated_at
                try:
                    update_result = await self.repository.execute_query(
                        """
                        UPDATE chat_sessions
                        SET
                            description = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                        """,
                        (description, session_id)
                    )
                    if update_result is not True:
                        logger.error(f"Failed to update session description for {session_id}")
                        return False
                    logger.info(f"Updated description for existing session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to update existing session {session_id}: {e}")
                    return False
            else:
                # Create new session if it doesn't exist - only use basic columns
                try:
                    insert_result = await self.repository.execute_query(
                        """
                        INSERT INTO chat_sessions (session_id, description, created_at, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (session_id, description)
                    )
                    if insert_result is not True:
                        logger.error(f"Failed to insert session description for {session_id}")
                        return False
                    logger.info(f"Created new session {session_id} with description")
                except Exception as e:
                    logger.error(f"Failed to insert new session {session_id}: {e}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error updating session description: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
    
    async def get_session_info(self, session_id: str, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get session information, create if not exists"""
        try:
            # 실제 데이터베이스 스키마에 맞게 수정 (존재하는 컬럼만 조회)
            result = await self.repository.execute_query(
                """
                SELECT session_id, user_id, title, description, created_at, updated_at
                FROM chat_sessions 
                WHERE session_id = %s
                """,
                (session_id,)
            )
            
            if result:
                row = result[0]
                user_id = row[1] if len(row) > 1 else user_id
                title = row[2] if len(row) > 2 else None
                description = row[3] if len(row) > 3 else None
                
                # 메시지 수는 별도로 계산
                message_count_result = await self.repository.execute_query(
                    """
                    SELECT COUNT(*) 
                    FROM chat_messages 
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )
                message_count = message_count_result[0][0] if message_count_result else 0
                
                # 마지막 활동 시간은 메시지의 최신 타임스탬프
                last_activity_result = await self.repository.execute_query(
                    """
                    SELECT MAX(created_at) 
                    FROM chat_messages 
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )
                last_activity = last_activity_result[0][0] if last_activity_result and last_activity_result[0][0] else None
                
                return {
                    "session_id": row[0],
                    "user_id": user_id,
                    "title": title,
                    "description": description,
                    "created_at": row[4].isoformat() if len(row) > 4 and row[4] else None,
                    "updated_at": row[5].isoformat() if len(row) > 5 and row[5] else None,
                    "last_activity": last_activity.isoformat() if last_activity else None,
                    "message_count": message_count
                }
            else:
                # 세션이 데이터베이스에 없으면 기본 제목으로 생성
                logger.info(f"Session {session_id} not found in database, creating with default title")
                default_title = "새 대화"
                await self.repository.execute_query(
                    """
                    INSERT INTO chat_sessions (session_id, user_id, title, title_edited, created_at, updated_at, last_activity)
                    VALUES (%s, %s, %s, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (session_id, user_id, default_title)
                )
                
                # 생성 후 다시 조회
                result = await self.repository.execute_query(
                    """
                    SELECT session_id, user_id, title, description, created_at, updated_at
                    FROM chat_sessions 
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )
                
                if result:
                    row = result[0]
                    # 메시지 수는 별도로 계산
                    message_count_result = await self.repository.execute_query(
                        """
                        SELECT COUNT(*) 
                        FROM chat_messages 
                        WHERE session_id = %s
                        """,
                        (session_id,)
                    )
                    message_count = message_count_result[0][0] if message_count_result else 0
                    
                    # 마지막 활동 시간은 메시지의 최신 타임스탬프
                    last_activity_result = await self.repository.execute_query(
                        """
                        SELECT MAX(created_at) 
                        FROM chat_messages 
                        WHERE session_id = %s
                        """,
                        (session_id,)
                    )
                    last_activity = last_activity_result[0][0] if last_activity_result and last_activity_result[0][0] else None
                    
                    return {
                        "session_id": row[0],
                        "user_id": row[1] if len(row) > 1 else user_id,
                        "title": row[2] if len(row) > 2 else default_title,
                        "description": row[3] if len(row) > 3 else None,
                        "created_at": row[4].isoformat() if len(row) > 4 and row[4] else None,
                        "updated_at": row[5].isoformat() if len(row) > 5 and row[5] else None,
                        "last_activity": last_activity.isoformat() if last_activity else None,
                        "message_count": message_count
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
