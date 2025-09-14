"""
Repository layer for chat data persistence
"""
from typing import List, Optional
from backend.models.chat import ChatSession, ChatMessage, MessageRole
import json
import os
from datetime import datetime

class ChatRepository:
    """Repository for chat session and message persistence"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def save_session(self, session: ChatSession) -> bool:
        """Save chat session to file"""
        try:
            session_file = os.path.join(self.data_dir, f"session_{session.id}.json")
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
                        "session_id": msg.session_id
                    }
                    for msg in session.messages
                ]
            }

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load chat session from file"""
        try:
            session_file = os.path.join(self.data_dir, f"session_{session_id}.json")
            if not os.path.exists(session_file):
                return None

            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            messages = [
                ChatMessage(
                    id=msg["id"],
                    role=MessageRole(msg["role"]),
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]),
                    session_id=msg["session_id"]
                )
                for msg in data["messages"]
            ]

            return ChatSession(
                id=data["id"],
                messages=messages,
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def get_all_sessions(self) -> List[str]:
        """Get all session IDs"""
        try:
            session_files = [f for f in os.listdir(self.data_dir) if f.startswith("session_")]
            return [f.replace("session_", "").replace(".json", "") for f in session_files]
        except Exception:
            return []

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists without loading all sessions"""
        try:
            session_file = os.path.join(self.data_dir, f"session_{session_id}.json")
            return os.path.exists(session_file)
        except Exception:
            return False
