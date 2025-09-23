"""
Hybrid chat repository that uses both file system and database
"""
import json
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from backend.models.chat import ChatSession, ChatMessage, MessageRole
from backend.services.database_service import DatabaseService
from sqlalchemy import text

logger = logging.getLogger(__name__)

class HybridChatRepository:
    """Hybrid repository that saves to both file system and database"""

    def __init__(self):
        self.db_service = DatabaseService()
        self.data_dir = "./data"
        self._initialized = False
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

    async def initialize(self):
        """Initialize database connection"""
        try:
            await self.db_service.initialize()
            self._initialized = True
            logger.info("HybridChatRepository initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize HybridChatRepository: {e}")
            # Continue with file-only mode if database fails
            self._initialized = False

    async def save_session(self, session: ChatSession) -> bool:
        """Save chat session to both file system and database"""
        try:
            # Always save to file system first (reliable)
            file_success = self._save_session_to_file(session)
            
            # Try to save to database if available
            db_success = True
            if self._initialized:
                try:
                    db_success = await self._save_session_to_db(session)
                except Exception as e:
                    logger.warning(f"Database save failed, using file only: {e}")
                    db_success = False
            
            return file_success and db_success
        except Exception as e:
            logger.error(f"Error saving session {session.id}: {e}")
            return False

    def _save_session_to_file(self, session: ChatSession) -> bool:
        """Save session to file system"""
        try:
            file_path = os.path.join(self.data_dir, f"session_{session.id}.json")
            
            session_data = {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "session_id": msg.session_id,
                        "metadata": msg.metadata or {}
                    }
                    for msg in session.messages
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Session {session.id} saved to file successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving session {session.id} to file: {e}")
            return False

    async def _save_session_to_db(self, session: ChatSession) -> bool:
        """Save session to database"""
        try:
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
                logger.info(f"Session {session.id} saved to database successfully")
                return True
        except Exception as e:
            logger.error(f"Error saving session {session.id} to database: {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load chat session from file system or database"""
        try:
            # Try to load from file system first
            session = self._load_session_from_file(session_id)
            if session:
                return session
            
            # If not found in file system, try database
            if self._initialized:
                return await self._load_session_from_db(session_id)
            
            return None
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None

    def _load_session_from_file(self, session_id: str) -> Optional[ChatSession]:
        """Load session from file system"""
        try:
            file_path = os.path.join(self.data_dir, f"session_{session_id}.json")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            messages = []
            for msg_data in session_data.get("messages", []):
                message = ChatMessage(
                    id=msg_data["id"],
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    session_id=msg_data["session_id"],
                    metadata=msg_data.get("metadata", {})
                )
                messages.append(message)
            
            return ChatSession(
                id=session_data["id"],
                messages=messages,
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"])
            )
        except Exception as e:
            logger.error(f"Error loading session {session_id} from file: {e}")
            return None

    async def _load_session_from_db(self, session_id: str) -> Optional[ChatSession]:
        """Load session from database"""
        try:
            async with self.db_service.get_session() as db_session:
                session_result = await db_session.execute(
                    text("SELECT id, created_at, updated_at FROM chat_sessions WHERE session_id = :session_id"),
                    {"session_id": session_id}
                )
                session_row = session_result.first()

                if not session_row:
                    return None

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
                    metadata = {}
                    if row.metadata:
                        try:
                            metadata = json.loads(row.metadata) if isinstance(row.metadata, str) else row.metadata
                        except:
                            metadata = {}
                    
                    message = ChatMessage(
                        id=str(row.id),
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
            logger.error(f"Error loading session {session_id} from database: {e}")
            return None

    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs from file system"""
        try:
            sessions = []
            for filename in os.listdir(self.data_dir):
                if filename.startswith("session_") and filename.endswith(".json"):
                    session_id = filename[8:-5]  # Remove "session_" prefix and ".json" suffix
                    sessions.append(session_id)
            
            # Sort by modification time (newest first)
            sessions.sort(key=lambda x: os.path.getmtime(os.path.join(self.data_dir, f"session_{x}.json")), reverse=True)
            return sessions
        except Exception as e:
            logger.error(f"Error getting all sessions: {e}")
            return []

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        try:
            file_path = os.path.join(self.data_dir, f"session_{session_id}.json")
            return os.path.exists(file_path)
        except Exception as e:
            logger.error(f"Error checking session existence for {session_id}: {e}")
            return False

    async def clear_session(self, session_id: str) -> bool:
        """Clear all messages from a chat session"""
        try:
            # Clear from file system
            file_path = os.path.join(self.data_dir, f"session_{session_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_data["messages"] = []
                session_data["updated_at"] = datetime.now().isoformat()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            # Clear from database if available
            if self._initialized:
                try:
                    async with self.db_service.get_session() as db_session:
                        await db_session.execute(
                            text("DELETE FROM chat_messages WHERE session_id = :session_id"),
                            {"session_id": session_id}
                        )
                        await db_session.execute(
                            text("UPDATE chat_sessions SET updated_at = :updated_at WHERE session_id = :session_id"),
                            {"updated_at": datetime.now(), "session_id": session_id}
                        )
                        await db_session.commit()
                except Exception as e:
                    logger.warning(f"Database clear failed: {e}")
            
            logger.info(f"Session {session_id} cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session completely"""
        try:
            # Delete from file system
            file_path = os.path.join(self.data_dir, f"session_{session_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete from database if available
            if self._initialized:
                try:
                    async with self.db_service.get_session() as db_session:
                        await db_session.execute(
                            text("DELETE FROM chat_messages WHERE session_id = :session_id"),
                            {"session_id": session_id}
                        )
                        await db_session.execute(
                            text("DELETE FROM chat_sessions WHERE session_id = :session_id"),
                            {"session_id": session_id}
                        )
                        await db_session.commit()
                except Exception as e:
                    logger.warning(f"Database delete failed: {e}")
            
            logger.info(f"Session {session_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def clear_all_sessions(self) -> List[str]:
        """Delete all sessions except 'default' from file system"""
        try:
            sessions_to_delete = []
            for filename in os.listdir(self.data_dir):
                if filename.startswith("session_") and filename.endswith(".json"):
                    session_id = filename[8:-5]
                    if session_id != "default":
                        sessions_to_delete.append(session_id)
            
            for session_id in sessions_to_delete:
                await self.delete_session(session_id)
            
            logger.info(f"Cleared {len(sessions_to_delete)} sessions (excluding default)")
            return sessions_to_delete
        except Exception as e:
            logger.error(f"Error clearing all sessions: {e}")
            return []

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        try:
            session = await self.load_session(session_id)
            if not session:
                return {"message_count": 0, "last_activity": None}
            
            last_activity = None
            if session.messages:
                last_activity = max(msg.timestamp for msg in session.messages)
            
            return {
                "message_count": len(session.messages),
                "last_activity": last_activity.isoformat() if last_activity else None
            }
        except Exception as e:
            logger.error(f"Error getting session stats for {session_id}: {e}")
            return {"message_count": 0, "last_activity": None}
