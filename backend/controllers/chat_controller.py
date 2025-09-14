"""
Chat controller for handling API requests
"""
import asyncio
from typing import Dict, Any

from backend.services.chat_service import ChatService
from backend.models.chat import ChatMessage


class ChatController:
    """Controller for chat-related endpoints"""

    def __init__(self):
        self.chat_service = ChatService()

    def create_session(self) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            session = self.chat_service.create_session()
            return {
                "success": True,
                "session_id": session.id,
                "created_at": session.created_at.isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Send a message and get response"""
        try:
            if not message.strip():
                return {
                    "success": False,
                    "error": "Message cannot be empty"
                }

            user_msg, assistant_msg = await self.chat_service.send_message(session_id, message)

            return {
                "success": True,
                "user_message": {
                    "id": user_msg.id,
                    "content": user_msg.content,
                    "timestamp": user_msg.timestamp.isoformat()
                },
                "assistant_message": {
                    "id": assistant_msg.id,
                    "content": assistant_msg.content,
                    "timestamp": assistant_msg.timestamp.isoformat()
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_chat_history(self, session_id: str, limit: int = None) -> Dict[str, Any]:
        """Get chat history for a session"""
        try:
            messages = self.chat_service.get_chat_history(session_id, limit)

            return {
                "success": True,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in messages
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_sessions(self) -> Dict[str, Any]:
        """Get all session IDs"""
        try:
            sessions = self.chat_service.get_all_sessions()
            return {
                "success": True,
                "sessions": sessions
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def check_session_exists(self, session_id: str) -> Dict[str, Any]:
        """Check if a session exists without loading all sessions"""
        try:
            exists = self.chat_service.session_exists(session_id)
            return {
                "success": True,
                "exists": exists
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a chat session"""
        try:
            success = self.chat_service.clear_session(session_id)
            return {
                "success": success,
                "message": "Session cleared successfully" if success else "Failed to clear session"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def clear_all_sessions(self) -> Dict[str, Any]:
        """Clear all sessions except default"""
        try:
            sessions = self.chat_service.get_all_sessions()
            cleared_sessions = []
            failed_sessions = []
            
            for session_id in sessions:
                if session_id != "default":  # Don't delete default session
                    success = self.chat_service.clear_session(session_id)
                    if success:
                        cleared_sessions.append(session_id)
                    else:
                        failed_sessions.append(session_id)
            
            return {
                "success": len(failed_sessions) == 0,
                "cleared_sessions": cleared_sessions,
                "failed_sessions": failed_sessions,
                "message": f"Cleared {len(cleared_sessions)} sessions successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
