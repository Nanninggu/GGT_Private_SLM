"""
Database-based chat repository for session and message persistence
"""
import uuid
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from backend.models.chat import ChatSession, ChatMessage, MessageRole
from backend.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class DBChatRepository:
    """Database-based repository for chat session and message persistence"""

    def __init__(self):
        self.db_service = DatabaseService()
        self._initialized = False

    async def initialize(self):
        """Initialize database connection"""
        await self.db_service.initialize()
        self._initialized = True

    async def save_session(self, session: ChatSession) -> bool:
        """Save chat session to database"""
        try:
            if not self._initialized:
                await self.initialize()
            
            logger.info(f"Saving session {session.id} with {len(session.messages)} messages")
            logger.info(f"Database service async_session_factory: {self.db_service.async_session_factory}")
            
            if self.db_service.async_session_factory is None:
                logger.error("Database service not properly initialized")
                return False
                
            async with self.db_service.get_session() as db_session:
                # Insert or update session
                await db_session.execute(
                    text("""
                        INSERT INTO chat_sessions (session_id, user_id, created_at, updated_at)
                        VALUES (:session_id, :user_id, :created_at, :updated_at)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET 
                            updated_at = :updated_at,
                            user_id = :user_id
                    """),
                    {
                        "session_id": session.id,
                        "user_id": session.user_id,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at
                    }
                )

                # Delete existing messages for this session
                await db_session.execute(
                    text("DELETE FROM chat_messages WHERE session_id = :session_id"),
                    {"session_id": session.id}
                )

                # Insert all messages
                for message in session.messages:
                    import json
                    # sources와 accuracy를 metadata에 포함시켜 저장
                    full_metadata = {
                        **(message.metadata or {}),
                        "sources": [
                            {
                                "filename": s.filename,
                                "similarity_score": s.similarity_score,
                                "content_preview": s.content_preview,
                                "document_id": s.document_id
                            }
                            for s in (message.sources or [])
                        ] if message.sources else [],
                        "accuracy": {
                            "confidence_score": message.accuracy.confidence_score,
                            "context_count": message.accuracy.context_count,
                            "avg_similarity": message.accuracy.avg_similarity,
                            "fallback_used": message.accuracy.fallback_used
                        } if message.accuracy else None
                    }
                    metadata_json = json.dumps(full_metadata)
                    await db_session.execute(
                        text("""
                            INSERT INTO chat_messages 
                            (id, session_id, role, content, metadata, created_at)
                            VALUES (:id, :session_id, :role, :content, :metadata, :created_at)
                        """),
                        {
                            "id": message.id,
                            "session_id": message.session_id,
                            "role": message.role.value,
                            "content": message.content,
                            "metadata": metadata_json,
                            "created_at": message.timestamp
                        }
                    )

                await db_session.commit()
                logger.info(f"Session {session.id} saved successfully")
                return True

        except Exception as e:
            logger.error(f"Error saving session {session.id}: {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load chat session from database"""
        try:
            async with self.db_service.get_session() as db_session:
                # Get session info
                session_result = await db_session.execute(
                    text("SELECT created_at, updated_at FROM chat_sessions WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                session_row = session_result.fetchone()
                
                if not session_row:
                    return None

                # Get messages
                messages_result = await db_session.execute(
                    text("""
                        SELECT id, role, content, metadata, created_at
                        FROM chat_messages 
                        WHERE session_id = :session_id 
                        ORDER BY created_at ASC
                    """),
                    {"session_id": session_id}
                )
                
                messages = []
                for row in messages_result:
                    import json
                    from backend.models.chat import SourceInfo, AccuracyInfo
                    
                    metadata = {}
                    if row.metadata:
                        try:
                            metadata = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
                        except:
                            metadata = {}
                    
                    # metadata에서 sources와 accuracy 복원
                    sources = []
                    if metadata.get("sources"):
                        sources = [
                            SourceInfo(
                                filename=s.get("filename", ""),
                                similarity_score=s.get("similarity_score", 0.0),
                                content_preview=s.get("content_preview", ""),
                                document_id=s.get("document_id", "")
                            )
                            for s in metadata["sources"]
                        ]
                    
                    accuracy = None
                    if metadata.get("accuracy"):
                        acc_data = metadata["accuracy"]
                        accuracy = AccuracyInfo(
                            confidence_score=acc_data.get("confidence_score", 0.0),
                            context_count=acc_data.get("context_count", 0),
                            avg_similarity=acc_data.get("avg_similarity", 0.0),
                            fallback_used=acc_data.get("fallback_used", False)
                        )
                    
                    # sources와 accuracy를 제거한 순수 metadata만 저장
                    clean_metadata = {k: v for k, v in metadata.items() if k not in ["sources", "accuracy"]}
                    
                    message = ChatMessage(
                        id=row.id,
                        role=MessageRole(row.role),
                        content=row.content,
                        timestamp=row.created_at,
                        session_id=session_id,
                        sources=sources,
                        accuracy=accuracy,
                        metadata=clean_metadata
                    )
                    messages.append(message)

                return ChatSession(
                    id=session_id,
                    messages=messages,
                    created_at=session_row.created_at,
                    updated_at=session_row.updated_at
                )

        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None

    async def get_all_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """Get all session IDs from database"""
        try:
            async with self.db_service.get_session() as db_session:
                if user_id:
                    query = text("SELECT session_id FROM chat_sessions WHERE user_id = :user_id ORDER BY created_at DESC")
                    params = {"user_id": user_id}
                else:
                    query = text("SELECT session_id FROM chat_sessions ORDER BY created_at DESC")
                    params = {}

                result = await db_session.execute(query, params)
                return [row.session_id for row in result]
        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")
            return []

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists in database"""
        try:
            async with self.db_service.get_session() as db_session:
                result = await db_session.execute(
                    text("SELECT 1 FROM chat_sessions WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking session existence {session_id}: {e}")
            return False

    async def clear_session(self, session_id: str) -> bool:
        """Clear all messages from a session"""
        try:
            async with self.db_service.get_session() as db_session:
                # Delete messages
                await db_session.execute(
                    text("DELETE FROM chat_messages WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                
                # Update session timestamp
                await db_session.execute(
                    text("""
                        UPDATE chat_sessions 
                        SET updated_at = :updated_at 
                        WHERE session_id = :session_id
                    """),
                    {
                        "session_id": session_id,
                        "updated_at": datetime.now()
                    }
                )
                
                await db_session.commit()
                logger.info(f"Session {session_id} cleared successfully")
                return True

        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session completely"""
        try:
            async with self.db_service.get_session() as db_session:
                # Delete messages first (foreign key constraint)
                await db_session.execute(
                    text("DELETE FROM chat_messages WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                
                # Delete session
                await db_session.execute(
                    text("DELETE FROM chat_sessions WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                
                await db_session.commit()
                logger.info(f"Session {session_id} deleted successfully")
                return True

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def clear_all_sessions(self) -> List[str]:
        """Clear all sessions except default"""
        try:
            async with self.db_service.get_session() as db_session:
                # Get all sessions except default
                result = await db_session.execute(
                    text("SELECT session_id FROM chat_sessions WHERE session_id != 'default'")
                )
                session_ids = [row.session_id for row in result]
                
                if session_ids:
                    # Delete all messages
                    await db_session.execute(
                        text("DELETE FROM chat_messages WHERE session_id != 'default'")
                    )
                    
                    # Delete all sessions except default
                    await db_session.execute(
                        text("DELETE FROM chat_sessions WHERE session_id != 'default'")
                    )
                    
                    await db_session.commit()
                    logger.info(f"Cleared {len(session_ids)} sessions")
                
                return session_ids

        except Exception as e:
            logger.error(f"Error clearing all sessions: {e}")
            return []

    async def get_session_stats(self, session_id: str) -> dict:
        """Get session statistics"""
        try:
            async with self.db_service.get_session() as db_session:
                # Get message count
                result = await db_session.execute(
                    text("SELECT COUNT(*) FROM chat_messages WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                message_count = result.scalar() or 0
                
                # Get last activity
                result = await db_session.execute(
                    text("""
                        SELECT MAX(created_at) 
                        FROM chat_messages 
                        WHERE session_id = :session_id
                    """),
                    {"session_id": session_id}
                )
                last_activity = result.scalar()
                
                return {
                    "message_count": message_count,
                    "last_activity": last_activity.isoformat() if last_activity else None
                }

        except Exception as e:
            logger.error(f"Error getting session stats {session_id}: {e}")
            return {"message_count": 0, "last_activity": None}
    
    async def execute_query(self, query: str, params: tuple = None) -> Optional[List]:
        """Execute a raw SQL query and return results"""
        try:
            if not self._initialized:
                await self.initialize()
            
            async with self.db_service.get_session() as db_session:
                if params:
                    # Convert tuple to dict for SQLAlchemy
                    param_dict = {}
                    for i, param in enumerate(params):
                        param_dict[f"param_{i}"] = param
                    # Replace %s with :param_0, :param_1, etc.
                    formatted_query = query
                    for i in range(len(params)):
                        formatted_query = formatted_query.replace("%s", f":param_{i}", 1)
                    result = await db_session.execute(text(formatted_query), param_dict)
                else:
                    result = await db_session.execute(text(query))
                
                # Commit for INSERT/UPDATE/DELETE queries
                query_upper = query.strip().upper()
                if any(query_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']):
                    await db_session.commit()
                    # For modification queries, return success indicator
                    return True

                # Fetch all results for SELECT queries
                rows = result.fetchall()
                return [row for row in rows]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None