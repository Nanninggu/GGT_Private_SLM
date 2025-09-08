"""
Utility functions for Streamlit frontend
"""
import streamlit as st
from typing import Any, Dict, List
import json
from datetime import datetime

class SessionManager:
    """Manage Streamlit session state"""

    @staticmethod
    def initialize_session():
        """Initialize session state variables"""
        defaults = {
            "session_id": None,
            "messages": [],
            "backend_connected": False,
            "current_model": "exaone3.5-2.4"
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def reset_session():
        """Reset session state"""
        for key in ["messages", "session_id"]:
            if key in st.session_state:
                del st.session_state[key]

    @staticmethod
    def get_session_data() -> Dict[str, Any]:
        """Get all session data"""
        return dict(st.session_state)

class MessageFormatter:
    """Format messages for display"""

    @staticmethod
    def format_message_content(content: str, max_length: int = 1000) -> str:
        """Format message content for display"""
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."

    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """Format timestamp for Korean display"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y년 %m월 %d일 %H:%M:%S")
        except:
            return timestamp

class UIHelpers:
    """UI helper functions"""

    @staticmethod
    def create_download_data(messages: List[Dict[str, Any]]) -> str:
        """Create downloadable chat data"""
        chat_data = {
            "exported_at": datetime.now().isoformat(),
            "session_id": st.session_state.get("session_id", "unknown"),
            "messages": messages
        }
        return json.dumps(chat_data, ensure_ascii=False, indent=2)

    @staticmethod
    def validate_input(text: str) -> tuple[bool, str]:
        """Validate user input"""
        if not text or not text.strip():
            return False, "메시지를 입력해주세요."

        if len(text) > 5000:
            return False, "메시지가 너무 깁니다. (최대 5000자)"

        return True, ""

    @staticmethod
    def show_model_info():
        """Display model information"""
        st.markdown("""
        ### 🧠 모델 정보
        - **모델명**: Exaone 3.5 2.4
        - **타입**: 로컬 SLM (Small Language Model)
        - **특징**: 한국어 특화 모델
        - **용도**: 일반적인 대화 및 질의응답
        """)

class ConfigManager:
    """Configuration management"""

    @staticmethod
    def get_api_config() -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "base_url": "http://localhost:8000",
            "timeout": 30,
            "max_retries": 3
        }

    @staticmethod
    def get_ui_config() -> Dict[str, Any]:
        """Get UI configuration"""
        return {
            "page_title": "Exaone 챗봇",
            "page_icon": "🤖",
            "layout": "wide",
            "theme": "light"
        }
