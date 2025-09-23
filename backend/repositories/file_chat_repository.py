"""
File-based chat repository for reliable chat history storage
"""
import json
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from backend.models.chat import ChatSession, ChatMessage, MessageRole

logger = logging.getLogger(__name__)

class FileChatRepository:
    """File-based repository for chat session and message persistence"""

    def __init__(self):
        self.data_dir = "./data"
        self._initialized = True  # File system doesn't need initialization
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

    async def initialize(self):
        """Initialize file system (no-op for file system)"""
        logger.info("FileChatRepository initialized successfully")

    async def save_session(self, session: ChatSession) -> bool:
        """Save chat session to file system"""
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
            
            logger.info(f"Session {session.id} saved to file successfully with {len(session.messages)} messages")
            return True
        except Exception as e:
            logger.error(f"Error saving session {session.id} to file: {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load chat session from file system"""
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
            file_path = os.path.join(self.data_dir, f"session_{session_id}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_data["messages"] = []
                session_data["updated_at"] = datetime.now().isoformat()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Session {session_id} cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session completely"""
        try:
            file_path = os.path.join(self.data_dir, f"session_{session_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
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
