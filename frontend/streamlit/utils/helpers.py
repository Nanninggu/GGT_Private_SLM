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

:root {
  --bg: #0f1724;
  --surface: #ffffff;
  --muted: #6b7280;
  --primary: #0ea5a3;
  --accent: #ef4444;
  --card-shadow: 0 6px 18px rgba(15,23,36,0.06);
  --radius: 12px;
  --gap: 1rem;
  --max-width: 1200px;
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

.stButton > button:active,
.stButton > button:focus {
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
  .block-container { 
    padding: 1rem; 
  }
  .page-title { 
    font-size: 1.4rem; 
  }
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


class DesignThemeManager:
    """디자인 테마 관리자 - 다양한 테마 스타일 제공"""
    
    def __init__(self):
        self.themes = {
            "enterprise": self._get_enterprise_theme(),
            "modern": self._get_modern_theme(),
            "minimal": self._get_minimal_theme(),
            "dark": self._get_dark_theme(),
            "material3": self._get_material3_theme(),
            "gemini": self._get_gemini_theme(),
            "shadcn": self._get_shadcn_theme(),
            "antd": self._get_antd_theme()
        }
    
    def _get_enterprise_theme(self):
        """엔터프라이즈 테마"""
        return f"<style>{ENTERPRISE_THEME_CSS}</style>"
    
    def _get_modern_theme(self):
        """모던 테마"""
        return """
        <style>
        /* Modern Theme Styles */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .main .block-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .stButton > button {
            border-radius: 25px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        </style>
        """
    
    def _get_minimal_theme(self):
        """미니멀 테마"""
        return """
        <style>
        /* Minimal Theme Styles */
        .stApp {
            background-color: #f8f9fa;
        }
        
        .main .block-container {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 2rem;
            margin: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }
        
        .stButton > button {
            border-radius: 6px;
            background-color: #6c757d;
            color: white;
            border: none;
            font-weight: 500;
        }
        
        .stTextInput > div > div > input {
            border-radius: 6px;
            border: 1px solid #dee2e6;
            padding: 0.5rem 0.75rem;
        }
        </style>
        """
    
    def _get_dark_theme(self):
        """다크 테마"""
        return """
        <style>
        /* Dark Theme Styles */
        .stApp {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        
        .main .block-container {
            background-color: #2d2d2d;
            border-radius: 12px;
            padding: 2rem;
            margin: 1rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }
        
        .stButton > button {
            border-radius: 8px;
            background-color: #4a4a4a;
            color: #ffffff;
            border: 1px solid #666666;
            font-weight: 600;
        }
        
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 1px solid #666666;
            background-color: #3a3a3a;
            color: #ffffff;
            padding: 0.75rem 1rem;
        }
        </style>
        """
    
    def _get_material3_theme(self):
        """Material Design 3 테마"""
        return """
        <style>
        /* Material Design 3 Theme */
        .stApp {
            background-color: #fefbff;
            font-family: 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        .stDecoration {display:none;}
        .stApp > header {display:none;}
        .stApp > div[data-testid="stToolbar"] {display:none;}
        .stApp > div[data-testid="stDecoration"] {display:none;}
        .stApp > div[data-testid="stStatusWidget"] {display:none;}
        .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarUserContent"] > div[data-testid="stSidebarNav"] > div[data-testid="stSidebarNavItems"] > div[data-testid="stSidebarNavLink"]:first-child {display:none;}
        .stApp > div[data-testid="stHeader"] {display:none;}
        
        /* Main content area */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            background-color: #fefbff;
            max-width: 1200px;
        }
        
        /* M3 Color System */
        :root {
            --md-sys-color-primary: #6750a4;
            --md-sys-color-on-primary: #ffffff;
            --md-sys-color-primary-container: #eaddff;
            --md-sys-color-on-primary-container: #21005d;
            --md-sys-color-secondary: #625b71;
            --md-sys-color-on-secondary: #ffffff;
            --md-sys-color-secondary-container: #e8def8;
            --md-sys-color-on-secondary-container: #1d192b;
            --md-sys-color-tertiary: #7d5260;
            --md-sys-color-on-tertiary: #ffffff;
            --md-sys-color-tertiary-container: #ffd8e4;
            --md-sys-color-on-tertiary-container: #31111d;
            --md-sys-color-error: #ba1a1a;
            --md-sys-color-on-error: #ffffff;
            --md-sys-color-error-container: #ffdad6;
            --md-sys-color-on-error-container: #410002;
            --md-sys-color-surface: #fefbff;
            --md-sys-color-on-surface: #1c1b1f;
            --md-sys-color-surface-variant: #e7e0ec;
            --md-sys-color-on-surface-variant: #49454f;
            --md-sys-color-outline: #79747e;
            --md-sys-color-outline-variant: #cac4d0;
            --md-sys-color-shadow: #000000;
            --md-sys-color-scrim: #000000;
            --md-sys-color-inverse-surface: #313033;
            --md-sys-color-inverse-on-surface: #f4eff4;
            --md-sys-color-inverse-primary: #d0bcff;
        }
        
        /* M3 Typography */
        .stApp {
            font-family: 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            line-height: 1.5;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 400;
            color: var(--md-sys-color-on-surface);
        }
        
        h1 { font-size: 2.25rem; font-weight: 400; }
        h2 { font-size: 1.5rem; font-weight: 400; }
        h3 { font-size: 1.25rem; font-weight: 500; }
        h4 { font-size: 1rem; font-weight: 500; }
        
        /* M3 Buttons */
        .stButton > button {
            background-color: var(--md-sys-color-primary);
            color: var(--md-sys-color-on-primary);
            border: none;
            border-radius: 20px;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: 500;
            text-transform: none;
            letter-spacing: 0.1px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            min-height: 40px;
        }
        
        .stButton > button:hover {
            background-color: var(--md-sys-color-primary);
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
            transform: translateY(-1px);
        }
        
        .stButton > button:active {
            transform: translateY(0);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        /* M3 Text Input */
        .stTextInput > div > div > input {
            background-color: var(--md-sys-color-surface);
            color: var(--md-sys-color-on-surface);
            border: 1px solid var(--md-sys-color-outline);
            border-radius: 4px;
            padding: 16px;
            font-size: 16px;
            font-weight: 400;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--md-sys-color-primary);
            border-width: 2px;
            outline: none;
            box-shadow: 0 0 0 1px var(--md-sys-color-primary);
        }
        
        .stTextInput > div > div > input::placeholder {
            color: var(--md-sys-color-on-surface-variant);
        }
        
        /* M3 Selectbox */
        .stSelectbox > div > div {
            background-color: var(--md-sys-color-surface);
            border: 1px solid var(--md-sys-color-outline);
            border-radius: 4px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: var(--md-sys-color-primary);
            border-width: 2px;
            box-shadow: 0 0 0 1px var(--md-sys-color-primary);
        }
        
        /* M3 Chat Messages */
        .stChatMessage {
            background-color: var(--md-sys-color-surface);
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--md-sys-color-outline-variant);
        }
        
        /* M3 Chat Input */
        .stChatInput > div {
            background-color: var(--md-sys-color-surface);
            border: 1px solid var(--md-sys-color-outline);
            border-radius: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        .stChatInput > div:focus-within {
            border-color: var(--md-sys-color-primary);
            border-width: 2px;
            box-shadow: 0 0 0 1px var(--md-sys-color-primary);
        }
        
        /* M3 Cards */
        .modern-card {
            background-color: var(--md-sys-color-surface);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--md-sys-color-outline-variant);
            margin-bottom: 16px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .modern-card:hover {
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08);
        }
        
        /* M3 Sidebar */
        .css-1d391kg {
            background-color: var(--md-sys-color-surface);
        }
        
        .css-1d391kg .css-1v0mbdj {
            background-color: var(--md-sys-color-surface);
            border-radius: 16px;
            margin: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--md-sys-color-outline-variant);
        }
        
        /* M3 Tabs */
        .stTabs > div > div > div > div {
            background-color: var(--md-sys-color-surface);
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--md-sys-color-outline-variant);
        }
        
        /* M3 Expander */
        .streamlit-expander {
            border: 1px solid var(--md-sys-color-outline-variant);
            border-radius: 8px;
            background-color: var(--md-sys-color-surface);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        /* M3 Radio Buttons */
        .stRadio > div > label {
            background-color: var(--md-sys-color-surface);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--md-sys-color-outline-variant);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 400;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        .stRadio > div > label:hover {
            border-color: var(--md-sys-color-primary);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
        }
        
        /* M3 Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 16px;
            font-size: 14px;
            font-weight: 500;
            border: 1px solid;
        }
        
        .status-online {
            background-color: var(--md-sys-color-primary-container);
            color: var(--md-sys-color-on-primary-container);
            border-color: var(--md-sys-color-primary);
        }
        
        .status-offline {
            background-color: var(--md-sys-color-error-container);
            color: var(--md-sys-color-on-error-container);
            border-color: var(--md-sys-color-error);
        }
        
        /* M3 Responsive Design */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 16px;
                margin: 8px;
            }
            
            .stButton > button {
                padding: 12px 20px;
                font-size: 16px;
            }
        }
        </style>
        """
    
    def _get_gemini_theme(self):
        """Gemini 스타일 테마 (M3 기반)"""
        return """
        <style>
        /* Gemini Theme - Material Design 3 based */
        .stApp {
            background-color: #fefbff;
            font-family: 'Google Sans', 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        .stDecoration {display:none;}
        .stApp > header {display:none;}
        .stApp > div[data-testid="stToolbar"] {display:none;}
        .stApp > div[data-testid="stDecoration"] {display:none;}
        .stApp > div[data-testid="stStatusWidget"] {display:none;}
        .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarUserContent"] > div[data-testid="stSidebarNav"] > div[data-testid="stSidebarNavItems"] > div[data-testid="stSidebarNavLink"]:first-child {display:none;}
        .stApp > div[data-testid="stHeader"] {display:none;}
        
        /* Main content area */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            background-color: #fefbff;
            max-width: 1200px;
        }
        
        /* Gemini Color System */
        :root {
            --gemini-primary: #4285f4;
            --gemini-on-primary: #ffffff;
            --gemini-primary-container: #e3f2fd;
            --gemini-on-primary-container: #0d47a1;
            --gemini-secondary: #34a853;
            --gemini-on-secondary: #ffffff;
            --gemini-secondary-container: #e8f5e8;
            --gemini-on-secondary-container: #1b5e20;
            --gemini-tertiary: #ea4335;
            --gemini-on-tertiary: #ffffff;
            --gemini-tertiary-container: #ffebee;
            --gemini-on-tertiary-container: #b71c1c;
            --gemini-surface: #fefbff;
            --gemini-on-surface: #1a1a1a;
            --gemini-surface-variant: #f5f5f5;
            --gemini-on-surface-variant: #5f6368;
            --gemini-outline: #dadce0;
            --gemini-outline-variant: #e8eaed;
            --gemini-shadow: #000000;
            --gemini-scrim: #000000;
        }
        
        /* Gemini Typography */
        .stApp {
            font-family: 'Google Sans', 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            line-height: 1.5;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Google Sans', 'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 400;
            color: var(--gemini-on-surface);
        }
        
        h1 { font-size: 2.25rem; font-weight: 400; }
        h2 { font-size: 1.5rem; font-weight: 400; }
        h3 { font-size: 1.25rem; font-weight: 500; }
        h4 { font-size: 1rem; font-weight: 500; }
        
        /* Gemini Buttons */
        .stButton > button {
            background-color: var(--gemini-primary);
            color: var(--gemini-on-primary);
            border: none;
            border-radius: 24px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            text-transform: none;
            letter-spacing: 0.25px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            min-height: 40px;
        }
        
        .stButton > button:hover {
            background-color: var(--gemini-primary);
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
            transform: translateY(-1px);
        }
        
        .stButton > button:active {
            transform: translateY(0);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        /* Gemini Text Input */
        .stTextInput > div > div > input {
            background-color: var(--gemini-surface);
            color: var(--gemini-on-surface);
            border: 1px solid var(--gemini-outline);
            border-radius: 8px;
            padding: 16px;
            font-size: 16px;
            font-weight: 400;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--gemini-primary);
            border-width: 2px;
            outline: none;
            box-shadow: 0 0 0 1px var(--gemini-primary);
        }
        
        .stTextInput > div > div > input::placeholder {
            color: var(--gemini-on-surface-variant);
        }
        
        /* Gemini Selectbox */
        .stSelectbox > div > div {
            background-color: var(--gemini-surface);
            border: 1px solid var(--gemini-outline);
            border-radius: 8px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: var(--gemini-primary);
            border-width: 2px;
            box-shadow: 0 0 0 1px var(--gemini-primary);
        }
        
        /* Gemini Chat Messages */
        .stChatMessage {
            background-color: var(--gemini-surface);
            border-radius: 20px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--gemini-outline-variant);
        }
        
        /* Gemini Chat Input */
        .stChatInput > div {
            background-color: var(--gemini-surface);
            border: 1px solid var(--gemini-outline);
            border-radius: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        .stChatInput > div:focus-within {
            border-color: var(--gemini-primary);
            border-width: 2px;
            box-shadow: 0 0 0 1px var(--gemini-primary);
        }
        
        /* Gemini Cards */
        .modern-card {
            background-color: var(--gemini-surface);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--gemini-outline-variant);
            margin-bottom: 16px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .modern-card:hover {
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08);
        }
        
        /* Gemini Sidebar */
        .css-1d391kg {
            background-color: var(--gemini-surface);
        }
        
        .css-1d391kg .css-1v0mbdj {
            background-color: var(--gemini-surface);
            border-radius: 16px;
            margin: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--gemini-outline-variant);
        }
        
        /* Gemini Tabs */
        .stTabs > div > div > div > div {
            background-color: var(--gemini-surface);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            border: 1px solid var(--gemini-outline-variant);
        }
        
        /* Gemini Expander */
        .streamlit-expander {
            border: 1px solid var(--gemini-outline-variant);
            border-radius: 12px;
            background-color: var(--gemini-surface);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        /* Gemini Radio Buttons */
        .stRadio > div > label {
            background-color: var(--gemini-surface);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid var(--gemini-outline-variant);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 400;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
        }
        
        .stRadio > div > label:hover {
            border-color: var(--gemini-primary);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08);
        }
        
        /* Gemini Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
            border: 1px solid;
        }
        
        .status-online {
            background-color: var(--gemini-primary-container);
            color: var(--gemini-on-primary-container);
            border-color: var(--gemini-primary);
        }
        
        .status-offline {
            background-color: var(--gemini-tertiary-container);
            color: var(--gemini-on-tertiary-container);
            border-color: var(--gemini-tertiary);
        }
        
        /* Gemini Responsive Design */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 16px;
                margin: 8px;
            }
            
            .stButton > button {
                padding: 12px 20px;
                font-size: 16px;
            }
        }
        </style>
        """
    
    def _get_shadcn_theme(self):
        """Shadcn UI 테마"""
        return """
        <style>
        /* Shadcn UI Theme */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        .stApp {
            background-color: hsl(0 0% 100%);
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
            color: hsl(222.2 84% 4.9%);
        }
        
        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        .stDecoration {display:none;}
        .stApp > header {display:none;}
        .stApp > div[data-testid="stToolbar"] {display:none;}
        .stApp > div[data-testid="stDecoration"] {display:none;}
        .stApp > div[data-testid="stStatusWidget"] {display:none;}
        .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarUserContent"] > div[data-testid="stSidebarNav"] > div[data-testid="stSidebarNavItems"] > div[data-testid="stSidebarNavLink"]:first-child {display:none;}
        .stApp > div[data-testid="stHeader"] {display:none;}
        
        /* Main content area */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            background-color: hsl(0 0% 100%);
            max-width: 1200px;
        }
        
        /* Shadcn Color System */
        :root {
            --background: 0 0% 100%;
            --foreground: 222.2 84% 4.9%;
            --card: 0 0% 100%;
            --card-foreground: 222.2 84% 4.9%;
            --popover: 0 0% 100%;
            --popover-foreground: 222.2 84% 4.9%;
            --primary: 221.2 83.2% 53.3%;
            --primary-foreground: 210 40% 98%;
            --secondary: 210 40% 96%;
            --secondary-foreground: 222.2 84% 4.9%;
            --muted: 210 40% 96%;
            --muted-foreground: 215.4 16.3% 46.9%;
            --accent: 210 40% 96%;
            --accent-foreground: 222.2 84% 4.9%;
            --destructive: 0 84.2% 60.2%;
            --destructive-foreground: 210 40% 98%;
            --border: 214.3 31.8% 91.4%;
            --input: 214.3 31.8% 91.4%;
            --ring: 221.2 83.2% 53.3%;
            --radius: 0.5rem;
        }
        
        /* Shadcn Typography */
        .stApp {
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
            font-size: 14px;
            line-height: 1.5;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
            font-weight: 600;
            color: hsl(var(--foreground));
        }
        
        h1 { font-size: 2.25rem; font-weight: 700; }
        h2 { font-size: 1.5rem; font-weight: 600; }
        h3 { font-size: 1.25rem; font-weight: 600; }
        h4 { font-size: 1rem; font-weight: 600; }
        
        /* Shadcn Buttons */
        .stButton > button {
            background-color: hsl(var(--primary));
            color: hsl(var(--primary-foreground));
            border: none;
            border-radius: calc(var(--radius) - 2px);
            padding: 0.5rem 1rem;
            font-size: 14px;
            font-weight: 500;
            text-transform: none;
            letter-spacing: 0.025em;
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            min-height: 40px;
            cursor: pointer;
        }
        
        .stButton > button:hover {
            background-color: hsl(var(--primary) / 0.9);
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }
        
        .stButton > button:active {
            transform: translateY(1px);
        }
        
        .stButton > button:focus-visible {
            outline: 2px solid hsl(var(--ring));
            outline-offset: 2px;
        }
        
        /* Shadcn Text Input */
        .stTextInput > div > div > input {
            background-color: hsl(var(--background));
            color: hsl(var(--foreground));
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) - 2px);
            padding: 0.5rem 0.75rem;
            font-size: 14px;
            font-weight: 400;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stTextInput > div > div > input:focus {
            border-color: hsl(var(--ring));
            outline: none;
            box-shadow: 0 0 0 2px hsl(var(--ring) / 0.2);
        }
        
        .stTextInput > div > div > input::placeholder {
            color: hsl(var(--muted-foreground));
        }
        
        /* Shadcn Selectbox */
        .stSelectbox > div > div {
            background-color: hsl(var(--background));
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) - 2px);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: hsl(var(--ring));
            box-shadow: 0 0 0 2px hsl(var(--ring) / 0.2);
        }
        
        /* Shadcn Chat Messages */
        .stChatMessage {
            background-color: hsl(var(--card));
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) + 2px);
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        }
        
        /* Shadcn Chat Input */
        .stChatInput > div {
            background-color: hsl(var(--background));
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) + 4px);
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        }
        
        .stChatInput > div:focus-within {
            border-color: hsl(var(--ring));
            box-shadow: 0 0 0 2px hsl(var(--ring) / 0.2);
        }
        
        /* Shadcn Cards */
        .modern-card {
            background-color: hsl(var(--card));
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) + 2px);
            padding: 1.5rem;
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            margin-bottom: 1rem;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .modern-card:hover {
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }
        
        /* Shadcn Sidebar */
        .css-1d391kg {
            background-color: hsl(var(--background));
        }
        
        .css-1d391kg .css-1v0mbdj {
            background-color: hsl(var(--card));
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) + 2px);
            margin: 1rem;
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        }
        
        /* Shadcn Tabs */
        .stTabs > div > div > div > div {
            background-color: hsl(var(--background));
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) - 2px);
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: hsl(var(--accent));
            color: hsl(var(--accent-foreground));
            border-radius: calc(var(--radius) - 2px);
        }
        
        /* Shadcn Expander */
        .streamlit-expander {
            border: 1px solid hsl(var(--border));
            border-radius: calc(var(--radius) - 2px);
            background-color: hsl(var(--card));
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        }
        
        /* Shadcn Radio Buttons */
        .stRadio > div > label {
            background-color: hsl(var(--card));
            padding: 0.75rem;
            border-radius: calc(var(--radius) - 2px);
            border: 1px solid hsl(var(--border));
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 400;
            box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        }
        
        .stRadio > div > label:hover {
            background-color: hsl(var(--accent));
            color: hsl(var(--accent-foreground));
        }
        
        .stRadio > div > label[data-testid="stRadio"] {
            background-color: hsl(var(--primary));
            color: hsl(var(--primary-foreground));
        }
        
        /* Shadcn Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: calc(var(--radius) - 2px);
            font-size: 14px;
            font-weight: 500;
            border: 1px solid;
        }
        
        .status-online {
            background-color: hsl(var(--primary) / 0.1);
            color: hsl(var(--primary));
            border-color: hsl(var(--primary) / 0.2);
        }
        
        .status-offline {
            background-color: hsl(var(--destructive) / 0.1);
            color: hsl(var(--destructive));
            border-color: hsl(var(--destructive) / 0.2);
        }
        
        /* Shadcn Badge */
        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 9999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 600;
            line-height: 1;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .badge-default {
            background-color: hsl(var(--primary));
            color: hsl(var(--primary-foreground));
        }
        
        .badge-secondary {
            background-color: hsl(var(--secondary));
            color: hsl(var(--secondary-foreground));
        }
        
        .badge-destructive {
            background-color: hsl(var(--destructive));
            color: hsl(var(--destructive-foreground));
        }
        
        .badge-outline {
            border: 1px solid hsl(var(--border));
            color: hsl(var(--foreground));
        }
        
        /* Shadcn Alert */
        .alert {
            position: relative;
            width: 100%;
            border-radius: calc(var(--radius) - 2px);
            border: 1px solid;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .alert-default {
            background-color: hsl(var(--background));
            border-color: hsl(var(--border));
            color: hsl(var(--foreground));
        }
        
        .alert-destructive {
            background-color: hsl(var(--destructive) / 0.1);
            border-color: hsl(var(--destructive) / 0.2);
            color: hsl(var(--destructive));
        }
        
        /* Shadcn Responsive Design */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem;
                margin: 0.5rem;
            }
            
            .stButton > button {
                padding: 0.75rem 1rem;
                font-size: 16px;
            }
        }
        </style>
        """
    
    def _get_antd_theme(self):
        """Ant Design 테마"""
        return """
        <style>
        /* Ant Design Theme Styles */
        .stApp {
            background-color: #f0f2f5;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #262626;
        }
        
        /* Global text color */
        .stApp, .stApp * {
            color: #262626;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #262626 !important;
        }
        
        /* Paragraphs and text */
        p, div, span {
            color: #262626;
        }
        
        /* Streamlit specific text elements */
        .stMarkdown, .stMarkdown * {
            color: #262626 !important;
        }
        
        .stText, .stText * {
            color: #262626 !important;
        }
        
        .stWrite, .stWrite * {
            color: #262626 !important;
        }
        
        .stInfo, .stInfo * {
            color: #262626 !important;
        }
        
        .stSuccess, .stSuccess * {
            color: #262626 !important;
        }
        
        .stWarning, .stWarning * {
            color: #262626 !important;
        }
        
        .stError, .stError * {
            color: #262626 !important;
        }
        
        /* Override any inherited colors */
        .stApp [class*="st"] {
            color: #262626 !important;
        }
        
        /* Hide Streamlit default UI elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        .stDecoration {display:none;}
        .stApp > header {display:none;}
        .stApp > div[data-testid="stToolbar"] {display:none;}
        .stApp > div[data-testid="stDecoration"] {display:none;}
        .stApp > div[data-testid="stStatusWidget"] {display:none;}
        .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarUserContent"] > div[data-testid="stSidebarNav"] > div[data-testid="stSidebarNavItems"] > div[data-testid="stSidebarNavLink"]:first-child {display:none;}
        .stApp > div[data-testid="stHeader"] {display:none;}
        
        /* Main content area */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            background-color: #ffffff;
            max-width: 1200px;
            margin: 0 auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid #d9d9d9;
            color: #262626;
        }
        
        /* Ensure text is visible in main content */
        .main .block-container * {
            color: #262626;
        }
        
        /* Page header */
        .page-header {
            background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
            color: white;
            padding: 2rem;
            border-radius: 6px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
        }
        
        .page-title {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .page-subtitle {
            font-size: 1rem;
            opacity: 0.9;
        }
        
        /* Buttons - Ant Design style */
        .stButton > button {
            background-color: #1890ff;
            color: white;
            border: 1px solid #1890ff;
            border-radius: 6px;
            padding: 4px 15px;
            font-size: 14px;
            font-weight: 400;
            height: 32px;
            transition: all 0.3s;
            box-shadow: 0 2px 0 rgba(0,0,0,0.045);
        }
        
        .stButton > button:hover {
            background-color: #40a9ff;
            border-color: #40a9ff;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
        }
        
        .stButton > button:active {
            background-color: #096dd9;
            border-color: #096dd9;
            transform: translateY(0);
        }
        
        /* Primary button */
        .stButton > button[kind="primary"] {
            background-color: #1890ff;
            border-color: #1890ff;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: #40a9ff;
            border-color: #40a9ff;
        }
        
        /* Secondary button */
        .stButton > button[kind="secondary"] {
            background-color: #ffffff;
            color: #1890ff;
            border-color: #d9d9d9;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background-color: #f0f8ff;
            border-color: #40a9ff;
            color: #40a9ff;
        }
        
        /* Text inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > textarea {
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            padding: 4px 11px;
            font-size: 14px;
            transition: all 0.3s;
            background-color: #ffffff;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > textarea:focus {
            border-color: #40a9ff;
            box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
            outline: none;
        }
        
        /* Select boxes */
        .stSelectbox > div > div {
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            background-color: #ffffff;
        }
        
        .stSelectbox > div > div:focus-within {
            border-color: #40a9ff;
            box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
        }
        
        /* Radio buttons */
        .stRadio > div {
            gap: 8px;
        }
        
        .stRadio > div > label {
            font-size: 14px;
            color: #262626 !important;
        }
        
        .stRadio > div > label > div {
            color: #262626 !important;
        }
        
        /* Checkboxes */
        .stCheckbox > label {
            color: #262626 !important;
        }
        
        .stCheckbox > label > div {
            color: #262626 !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background-color: #fafafa;
            border-radius: 6px;
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 400;
            color: #8c8c8c !important;
            transition: all 0.3s;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #ffffff;
            color: #1890ff !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: #1890ff !important;
        }
        
        /* Sidebar */
        .stSidebar {
            background-color: #ffffff;
            border-right: 1px solid #f0f0f0;
            color: #262626;
        }
        
        .stSidebar * {
            color: #262626;
        }
        
        .stSidebar .stSelectbox > div > div {
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            background-color: #ffffff;
            color: #262626;
        }
        
        .stSidebar .stSelectbox > div > div:focus-within {
            border-color: #40a9ff;
            box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
        }
        
        /* Cards and containers */
        .config-section {
            background-color: #ffffff;
            border: 1px solid #f0f0f0;
            border-radius: 6px;
            padding: 24px;
            margin-bottom: 16px;
            color: #262626;
        }
        
        .config-section * {
            color: #262626;
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online {
            background-color: #52c41a;
        }
        
        .status-offline {
            background-color: #ff4d4f;
        }
        
        /* Alerts and messages */
        .stAlert {
            border-radius: 6px;
            border: 1px solid;
        }
        
        .stAlert[data-testid="alert-success"] {
            background-color: #f6ffed;
            border-color: #b7eb8f;
            color: #389e0d;
        }
        
        .stAlert[data-testid="alert-error"] {
            background-color: #fff2f0;
            border-color: #ffccc7;
            color: #cf1322;
        }
        
        .stAlert[data-testid="alert-warning"] {
            background-color: #fffbe6;
            border-color: #ffe58f;
            color: #d48806;
        }
        
        .stAlert[data-testid="alert-info"] {
            background-color: #e6f7ff;
            border-color: #91d5ff;
            color: #0958d9;
        }
        
        /* Tables */
        .stDataFrame {
            border: 1px solid #f0f0f0;
            border-radius: 6px;
        }
        
        /* Progress bars */
        .stProgress > div > div > div {
            background-color: #1890ff;
        }
        
        /* File uploader */
        .stFileUploader > div {
            border: 1px dashed #d9d9d9;
            border-radius: 6px;
            background-color: #fafafa;
        }
        
        .stFileUploader > div:hover {
            border-color: #40a9ff;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background-color: #fafafa;
            border: 1px solid #f0f0f0;
            border-radius: 6px;
            font-weight: 500;
        }
        
        .streamlit-expanderContent {
            border: 1px solid #f0f0f0;
            border-top: none;
            border-radius: 0 0 6px 6px;
        }
        
        /* Chat messages */
        .chat-message {
            background-color: #ffffff;
            border: 1px solid #f0f0f0;
            border-radius: 6px;
            padding: 12px 16px;
            margin: 8px 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            color: #262626;
        }
        
        .chat-message.user {
            background-color: #e6f7ff;
            border-color: #91d5ff;
            color: #262626;
        }
        
        .chat-message.assistant {
            background-color: #f6ffed;
            border-color: #b7eb8f;
            color: #262626;
        }
        
        .chat-message * {
            color: #262626;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main .block-container {
                margin: 0.5rem;
                padding: 1rem;
            }
            
            .page-header {
                padding: 1.5rem;
            }
            
            .page-title {
                font-size: 1.5rem;
            }
        }
        </style>
        """
    
    def apply_theme(self, theme_name: str):
        """테마 적용"""
        if theme_name in self.themes:
            # 테마에 이미 <style> 태그가 포함되어 있으므로 그대로 사용
            st.markdown(self.themes[theme_name], unsafe_allow_html=True)
    
    def apply_custom_theme(self, settings: Dict[str, Any]):
        """커스텀 테마 적용"""
        # 커스텀 테마 로직은 기존과 동일하게 유지
        pass

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
        /* Hide Streamlit default header elements completely */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none !important;}
        .stDecoration {display: none !important;}
        .stApp > header {display: none !important;}
        .stApp > div[data-testid="stToolbar"] {display: none !important;}
        .stApp > div[data-testid="stDecoration"] {display: none !important;}
        .stApp > div[data-testid="stStatusWidget"] {display: none !important;}
        
        /* Hide the hamburger menu */
        .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarUserContent"] > div[data-testid="stSidebarNav"] > div[data-testid="stSidebarNavItems"] > div[data-testid="stSidebarNavLink"]:first-child {display: none !important;}
        
        /* Hide the top bar completely */
        .stApp > div[data-testid="stHeader"] {display: none !important;}
        
        /* Hide all header related elements */
        .stApp > div[data-testid="stHeader"] > div[data-testid="stToolbar"] {display: none !important;}
        .stApp > div[data-testid="stHeader"] > div[data-testid="stDecoration"] {display: none !important;}
        
        /* Hide action buttons and deploy button */
        .stActionButton {display: none !important;}
        .stDeployButton {display: none !important;}
        
        /* Hide status widget */
        .stStatusWidget {display: none !important;}
        
        /* Ensure content starts from top */
        .stApp > div[data-testid="stAppViewContainer"] {
            padding-top: 0 !important;
        }
        
        /* Hide the main menu */
        .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarContent"] > div[data-testid="stSidebarNav"] {
            display: none !important;
        }
        
        /* Additional comprehensive hiding */
        [data-testid="stHeader"] {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        [data-testid="stStatusWidget"] {display: none !important;}
        
        /* Hide any remaining header elements */
        .stApp header {display: none !important;}
        .stApp .stDeployButton {display: none !important;}
        .stApp .stActionButton {display: none !important;}
        
        /* Ensure no spacing from hidden elements */
        .main .block-container {
            padding-top: 1rem !important;
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

class FontManager:
    """폰트 설정 관리자"""
    
    def __init__(self):
        self.font_families = {
            "Inter": "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial",
            "Roboto": "Roboto, 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            "Google Sans": "Google Sans, Roboto, 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            "Noto Sans KR": "Noto Sans KR, sans-serif",
            "Pretendard": "Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif",
            "Arial": "Arial, sans-serif",
            "Helvetica": "Helvetica, Arial, sans-serif",
            "Times New Roman": "Times New Roman, serif",
            "Georgia": "Georgia, serif",
            "Courier New": "Courier New, monospace"
        }
        
        self.font_weights = {
            "100": "100",
            "200": "200", 
            "300": "300",
            "400": "400",
            "500": "500",
            "600": "600",
            "700": "700",
            "800": "800",
            "900": "900"
        }
        
        self.font_sizes = {
            "10px": "10px",
            "12px": "12px",
            "14px": "14px",
            "16px": "16px",
            "18px": "18px",
            "20px": "20px",
            "24px": "24px",
            "28px": "28px",
            "32px": "32px",
            "0.8rem": "0.8rem",
            "0.85rem": "0.85rem",
            "0.9rem": "0.9rem",
            "0.95rem": "0.95rem",
            "1rem": "1rem",
            "1.1rem": "1.1rem",
            "1.2rem": "1.2rem",
            "1.3rem": "1.3rem",
            "1.4rem": "1.4rem",
            "1.5rem": "1.5rem",
            "1.6rem": "1.6rem",
            "1.7rem": "1.7rem",
            "1.8rem": "1.8rem",
            "1.9rem": "1.9rem",
            "2rem": "2rem",
            "2.25rem": "2.25rem",
            "2.5rem": "2.5rem",
            "3rem": "3rem"
        }
    
    def load_font_settings(self) -> Dict[str, Any]:
        """폰트 설정 로드"""
        try:
            with open("data/theme_settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                return settings.get("font_settings", self.get_default_font_settings())
        except:
            return self.get_default_font_settings()
    
    def save_font_settings(self, font_settings: Dict[str, Any]):
        """폰트 설정 저장"""
        try:
            # 기존 설정 로드
            with open("data/theme_settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            # 폰트 설정 업데이트
            settings["font_settings"] = font_settings
            settings["last_updated"] = datetime.now().isoformat()
            
            # 저장
            with open("data/theme_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"폰트 설정 저장 중 오류: {e}")
            return False
    
    def get_default_font_settings(self) -> Dict[str, Any]:
        """기본 폰트 설정 반환"""
        return {
            "global_font": {
                "family": "Inter",
                "size": "14px",
                "weight": "400",
                "line_height": "1.5"
            },
            "menu_fonts": {
                "main_menu": {
                    "family": "Inter",
                    "size": "16px",
                    "weight": "600"
                },
                "sub_menu": {
                    "family": "Inter", 
                    "size": "14px",
                    "weight": "500"
                },
                "page_title": {
                    "family": "Inter",
                    "size": "1.9rem",
                    "weight": "800"
                },
                "page_subtitle": {
                    "family": "Inter",
                    "size": "0.95rem",
                    "weight": "400"
                }
            },
            "content_fonts": {
                "body_text": {
                    "family": "Inter",
                    "size": "14px",
                    "weight": "400"
                },
                "button_text": {
                    "family": "Inter",
                    "size": "14px",
                    "weight": "600"
                },
                "input_text": {
                    "family": "Inter",
                    "size": "16px",
                    "weight": "400"
                }
            }
        }
    
    def generate_font_css(self, font_settings: Dict[str, Any]) -> str:
        """폰트 설정을 CSS로 변환"""
        css = ""
        
        # Google Fonts import
        used_fonts = set()
        for category in font_settings.values():
            if isinstance(category, dict):
                for font_config in category.values():
                    if isinstance(font_config, dict) and "family" in font_config:
                        font_family = font_config["family"]
                        if font_family in ["Google Sans", "Roboto", "Noto Sans KR"]:
                            used_fonts.add(font_family)
        
        if used_fonts:
            font_imports = []
            if "Google Sans" in used_fonts:
                font_imports.append("Google+Sans:wght@300;400;500;600;700;800")
            if "Roboto" in used_fonts:
                font_imports.append("Roboto:wght@300;400;500;600;700;800")
            if "Noto Sans KR" in used_fonts:
                font_imports.append("Noto+Sans+KR:wght@300;400;500;600;700;800")
            
            if font_imports:
                css += f"@import url('https://fonts.googleapis.com/css2?family={';'.join(font_imports)}&display=swap');\n\n"
        
        # 전역 폰트 설정
        global_font = font_settings.get("global_font", {})
        if global_font:
            font_family = self.font_families.get(global_font.get("family", "Inter"), global_font.get("family", "Inter"))
            font_size = global_font.get("size", "14px")
            font_weight = global_font.get("weight", "400")
            line_height = global_font.get("line_height", "1.5")
            
            css += f"""
.stApp {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
    line-height: {line_height};
}}
"""
        
        # 메뉴 폰트 설정
        menu_fonts = font_settings.get("menu_fonts", {})
        for menu_type, config in menu_fonts.items():
            if isinstance(config, dict):
                font_family = self.font_families.get(config.get("family", "Inter"), config.get("family", "Inter"))
                font_size = config.get("size", "14px")
                font_weight = config.get("weight", "400")
                
                if menu_type == "main_menu":
                    css += f"""
.stSidebar .css-1d391kg .css-1v0mbdj .css-1v0mbdj > div > div > div > div {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
}}
"""
                elif menu_type == "sub_menu":
                    css += f"""
.stSidebar .css-1d391kg .css-1v0mbdj .css-1v0mbdj > div > div > div > div > div {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
}}
"""
                elif menu_type == "page_title":
                    css += f"""
.page-title {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
}}
"""
                elif menu_type == "page_subtitle":
                    css += f"""
.page-subtitle {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
}}
"""
        
        # 콘텐츠 폰트 설정
        content_fonts = font_settings.get("content_fonts", {})
        for content_type, config in content_fonts.items():
            if isinstance(config, dict):
                font_family = self.font_families.get(config.get("family", "Inter"), config.get("family", "Inter"))
                font_size = config.get("size", "14px")
                font_weight = config.get("weight", "400")
                
                if content_type == "body_text":
                    css += f"""
.stMarkdown, .stText, .stWrite {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
}}
"""
                elif content_type == "button_text":
                    css += f"""
.stButton > button {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
}}
"""
                elif content_type == "input_text":
                    css += f"""
.stTextInput > div > div > input,
.stTextArea > div > textarea,
.stSelectbox > div > div {{
    font-family: {font_family};
    font-size: {font_size};
    font-weight: {font_weight};
}}
"""
        
        return css
    
    def apply_font_settings(self, font_settings: Dict[str, Any]):
        """폰트 설정 적용"""
        css = self.generate_font_css(font_settings)
        if css:
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


class ConfigManager:
    """Configuration management"""

    @staticmethod
    def get_api_config() -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "base_url": "http://localhost:9502",
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
