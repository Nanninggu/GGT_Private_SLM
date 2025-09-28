"""
Utility functions for the backend
"""
import json
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
