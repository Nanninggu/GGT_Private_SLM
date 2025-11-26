"""
Chat message models for the chatbot application
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class SourceInfo:
    """Source information for RAG responses"""
    filename: str
    similarity_score: float
    content_preview: str
    document_id: str

@dataclass
class AccuracyInfo:
    """Accuracy information for responses"""
    confidence_score: float
    context_count: int
    avg_similarity: float
    fallback_used: bool = False

@dataclass
class ChatMessage:
    """Chat message model"""
    id: Optional[str] = None
    role: MessageRole = MessageRole.USER
    content: str = ""
    timestamp: datetime = None
    session_id: Optional[str] = None
    sources: List[SourceInfo] = field(default_factory=list)
    accuracy: Optional[AccuracyInfo] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

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
    user_id: Optional[str] = None

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
