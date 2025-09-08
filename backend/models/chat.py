"""
Chat message models for the chatbot application
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class ChatMessage:
    """Chat message model"""
    id: Optional[str] = None
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = None
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ChatSession:
    """Chat session model"""
    id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

    def add_message(self, message: ChatMessage):
        """Add a message to the session"""
        message.session_id = self.id
        self.messages.append(message)
        self.updated_at = datetime.now()

@dataclass
class ModelResponse:
    """Model response wrapper"""
    content: str
    tokens_used: int
    response_time: float
    model_name: str
