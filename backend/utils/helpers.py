"""
Utility functions for the backend
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict
from backend.config.settings import settings

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chatbot.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_message(message: str) -> bool:
    """Validate user message"""
    if not message or not message.strip():
        return False
    if len(message) > 5000:  # Max message length
        return False
    return True

def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    # Remove potentially harmful characters
    sanitized = text.strip()
    # Add more sanitization as needed
    return sanitized

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
