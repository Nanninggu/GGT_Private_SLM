"""
Chat controller for handling API requests
"""
import asyncio
from typing import Dict, Any

from backend.services.chat_service import ChatService
from backend.services.ollama_service import ollama_service
from backend.models.chat import ChatMessage, MessageRole


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

    async def send_message(self, session_id: str, message: str, model_type: str = "fast") -> Dict[str, Any]:
        """Send a message and get response with model selection"""
        try:
            if not message.strip():
                return {
                    "success": False,
                    "error": "Message cannot be empty"
                }

            user_msg, assistant_msg = await self.chat_service.send_message(session_id, message, model_type)

            # Format sources for response
            sources_data = []
            if assistant_msg.sources:
                for source in assistant_msg.sources:
                    sources_data.append({
                        "filename": source.filename,
                        "similarity_score": source.similarity_score,
                        "content_preview": source.content_preview,
                        "document_id": source.document_id
                    })
            
            # Format accuracy info for response
            accuracy_data = None
            if assistant_msg.accuracy:
                accuracy_data = {
                    "confidence_score": assistant_msg.accuracy.confidence_score,
                    "context_count": assistant_msg.accuracy.context_count,
                    "avg_similarity": assistant_msg.accuracy.avg_similarity,
                    "fallback_used": assistant_msg.accuracy.fallback_used
                }
            
            # Get model info from metadata
            model_info = assistant_msg.metadata.get("model_info", {}) if assistant_msg.metadata else {}
            
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
                    "timestamp": assistant_msg.timestamp.isoformat(),
                    "sources": sources_data,
                    "accuracy": accuracy_data,
                    "metadata": assistant_msg.metadata,
                    "model_info": model_info
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

            formatted_messages = []
            for msg in messages:
                message_data = {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                
                # Add source and accuracy info for assistant messages
                if msg.role == MessageRole.ASSISTANT:
                    # Format sources
                    sources_data = []
                    if msg.sources:
                        for source in msg.sources:
                            sources_data.append({
                                "filename": source.filename,
                                "similarity_score": source.similarity_score,
                                "content_preview": source.content_preview,
                                "document_id": source.document_id
                            })
                    
                    # Format accuracy info
                    accuracy_data = None
                    if msg.accuracy:
                        accuracy_data = {
                            "confidence_score": msg.accuracy.confidence_score,
                            "context_count": msg.accuracy.context_count,
                            "avg_similarity": msg.accuracy.avg_similarity,
                            "fallback_used": msg.accuracy.fallback_used
                        }
                    
                    message_data.update({
                        "sources": sources_data,
                        "accuracy": accuracy_data,
                        "metadata": msg.metadata
                    })
                
                formatted_messages.append(message_data)
            
            return {
                "success": True,
                "messages": formatted_messages
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Get available models for selection"""
        try:
            models = await ollama_service.get_available_models()
            return {
                "success": True,
                "models": models
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Get configuration for a specific model type"""
        try:
            config = await ollama_service.get_model_config(model_type)
            return {
                "success": True,
                "config": config
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
