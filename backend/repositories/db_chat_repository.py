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
                        INSERT INTO chat_sessions (session_id, created_at, updated_at)
                        VALUES (:session_id, :created_at, :updated_at)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET 
                            updated_at = :updated_at
                    """),
                    {
                        "session_id": session.id,
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
                    metadata_json = json.dumps(message.metadata or {})
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
                    metadata = {}
                    if row.metadata:
                        try:
                            metadata = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
                        except:
                            metadata = {}
                    
                    message = ChatMessage(
                        id=row.id,
                        role=MessageRole(row.role),
                        content=row.content,
                        timestamp=row.created_at,
                        session_id=session_id,
                        metadata=metadata
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

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs from database"""
        try:
            async with self.db_service.get_session() as db_session:
                result = await db_session.execute(
                    text("SELECT session_id FROM chat_sessions ORDER BY created_at DESC")
                )
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
                
                # Fetch all results
                rows = result.fetchall()
                return [row for row in rows]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None