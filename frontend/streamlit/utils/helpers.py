"""
Utility functions for Streamlit frontend
"""
import streamlit as st
from typing import Any, Dict, List
import json
from datetime import datetime

# 엔터프라이즈 테마 CSS
ENTERPRISE_THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

:root{
  --bg:#0f1724; /* optional dark base, 바꾸려면 #ffffff */
  --surface:#ffffff;
  --muted:#6b7280;
  --primary:#0ea5a3; /* teal */
  --accent:#ef4444;
  --card-shadow: 0 6px 18px rgba(15,23,36,0.06);
  --radius:12px;
  --gap:1rem;
  --max-width:1200px;
}

/* 전체 레이아웃 */
.stApp {
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  background: linear-gradient(180deg, #f7fafc 0%, #ffffff 100%);
  color: #0f1724;
}

/* 중앙 컨테이너 폭 제한(엔터프라이즈 레이아웃) */
.block-container {
  max-width: var(--max-width) !important;
  padding: 2rem 2rem !important;
}

/* 헤더 */
.page-header {
  background: linear-gradient(90deg, rgba(14,165,163,0.06), rgba(239,68,68,0.03));
  border-radius: calc(var(--radius) * 1.5);
  padding: 2.4rem 1.6rem;
  box-shadow: var(--card-shadow);
  margin-bottom: 1.5rem;
  text-align: left;
}
.page-title {
  font-size: 1.9rem;
  font-weight: 800;
  color: #0f1724;
  margin-bottom: 0.15rem;
}
.page-subtitle {
  color: var(--muted);
  font-size: 0.95rem;
}

/* 카드 */
.config-section, .status-card, .collection-card, .session-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 1.4rem;
  box-shadow: var(--card-shadow);
  margin-bottom: 1rem;
  border: 1px solid rgba(15,23,36,0.04);
}

/* 버튼 */
.stButton > button {
  border-radius: 10px;
  padding: 0.6rem 1rem;
  font-weight: 600;
  color: #fff;
  background: var(--primary);
  border: none;
  box-shadow: 0 6px 12px rgba(14,165,163,0.12);
}
.stButton > button:active, .stButton > button:focus {
  transform: translateY(1px);
}
.stButton > button[aria-disabled="true"] {
  background: #e6eef0;
  color: #9aa6ad;
  box-shadow: none;
}

/* 입력 */
.stTextInput > div > div > input,
.stTextArea > div > textarea,
.stSelectbox > div > div {
  border-radius: 10px;
  border: 1px solid rgba(15,23,36,0.08);
  padding: 0.75rem 1rem;
  background: #fff;
  font-size: 0.95rem;
  color: #0f1724;
}

/* 탭 - 선택 시 강조 색상 */
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: var(--accent);
  font-weight: 700;
}

/* 메시지 카드 스타일 (챗 미리보기 등) */
.message-card {
  background: linear-gradient(180deg, #ffffff, #fbfdff);
  border-radius: 10px;
  padding: 0.85rem;
  border: 1px solid rgba(14,165,163,0.06);
  margin-bottom: 0.6rem;
}

/* 반응형: 모바일에서 패딩 줄임 */
@media (max-width: 768px) {
  .block-container { padding: 1rem; }
  .page-title { font-size: 1.4rem; }
}
"""

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
    
    @staticmethod
    def save_current_session(*args, **kwargs):
        """Save current session to persistent storage"""
        try:
            # This is a placeholder for session persistence
            # In a real implementation, you would save to file, database, etc.
            # Accept any arguments for backward compatibility
            pass
        except Exception as e:
            print(f"세션 저장 중 오류: {e}")


class UIHelpers:
    """UI helper functions"""

    @staticmethod
    def load_enterprise_theme():
        """전역 CSS를 Streamlit에 주입합니다."""
        st.markdown(f"<style>{ENTERPRISE_THEME_CSS}</style>", unsafe_allow_html=True)

    @staticmethod
    def hide_streamlit_header():
        """Hide Streamlit default header elements (Deploy button, hamburger menu, top bar)"""
        st.markdown("""
        <style>
        /* Hide Streamlit default header elements */
        .stDeployButton {
            display: none;
        }
        
        /* Hide hamburger menu */
        .stActionButton {
            display: none;
        }
        
        /* Hide top bar */
        .stApp > header {
            display: none;
        }
        
        /* Hide the main menu button */
        .stApp > div[data-testid="stHeader"] {
            display: none;
        }
        
        /* Additional header hiding */
        .stApp > div[data-testid="stToolbar"] {
            display: none;
        }
        
        /* Hide the hamburger menu button */
        .stApp > div[data-testid="stHeader"] > div[data-testid="stToolbar"] {
            display: none;
        }
        
        /* Ensure content starts from top */
        .stApp > div[data-testid="stAppViewContainer"] {
            padding-top: 0;
        }
        
        /* Hide the main menu */
        .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarContent"] > div[data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)

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
            "base_url": "http://localhost:8002",
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
