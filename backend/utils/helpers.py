"""
Utility functions for the backend
"""
import json
import uuid
from datetime import datetime
from typing import Any, Dict


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

def generate_session_id(user_id: str = "default") -> str:
    """Generate custom session ID based on user ID and timestamp
    
    Format: chat_{user_short}_{YYYY}-{MM}-{DD}_{HH}:{MM}_{random4chars}
    Example: chat_user1_2024-12-15_14:30_a1b2
    """
    # Get current timestamp
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")  # YYYY-MM-DD format
    time_str = now.strftime("%H:%M")     # HH:MM format
    
    # Generate short random suffix (4 characters)
    random_suffix = str(uuid.uuid4()).replace("-", "")[:4]
    
    # Clean user_id (remove special characters that might cause issues)
    # Use shorter version for readability
    clean_user_id = user_id.replace("-", "").replace("_", "")[:8] if user_id else "default"
    
    # Format: chat_{user_short}_{date}_{time}_{random}
    session_id = f"chat_{clean_user_id}_{date_str}_{time_str}_{random_suffix}"
    
    return session_id
