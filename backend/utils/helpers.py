"""
Utility functions for the backend
"""
import json
from datetime import datetime
from typing import Any, Dict

"""
    예상 인풋값:
    - dt: datetime 객체 (예: datetime(2025, 10, 5, 14, 48, 0))
    예상 아웃풋값(리턴값):
    - 포맷된 문자열: "YYYY-MM-DD HH:MM:SS" (예: "2025-10-05 14:48:00")
"""
def format_timestamp(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

"""
    예상 인풋값:
    - text: 문자열 (예: "  hello <script>  ")

    예상 아웃풋값(리턴값):
    - 입력이 None 또는 빈 문자열일 경우: "" (빈 문자열)
    - 그 외: 앞뒤 공백이 제거된 문자열 (예: "hello <script>")
    - 향후 필요에 따라 추가 정규화나 이스케이프 처리로 확장 가능
"""
def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    # Remove potentially harmful characters
    sanitized = text.strip()
    # Add more sanitization as needed
    return sanitized

"""
    예상 인풋값:
    - obj: datetime 객체 또는 JSON으로 직렬화 가능한 기타 값
    예상 아웃풋값(리턴값):
    - datetime 입력 시: ISO 8601 형식의 문자열 (예: "2025-10-05T14:48:00")
    - 그 외: 부모 클래스의 default를 호출하여 해당 객체를 처리하거나 TypeError 발생
"""
class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
