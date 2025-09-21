"""
Login page for HAI Portal
"""
import streamlit as st
import requests
import json
import sys
import os
from datetime import datetime, timedelta

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_service import APIService

# Page configuration is handled in main.py

def login_user(username: str, password: str) -> dict:
    """Login user via API"""
    try:
        api_service = APIService()
        response = api_service.login(username, password)
        return response
    except Exception as e:
        return {
            "success": False,
            "message": f"로그인 중 오류가 발생했습니다: {str(e)}"
        }

def register_user(username: str, email: str, password: str, confirm_password: str) -> dict:
    """Register user via API"""
    try:
        api_service = APIService()
        response = api_service.register(username, email, password, confirm_password)
        return response
    except Exception as e:
        return {
            "success": False,
            "message": f"회원가입 중 오류가 발생했습니다: {str(e)}"
        }

def main():
    """Main login page function"""
    
    # HAI Portal styling - Login page
    st.markdown("""
    <style>
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
    
    /* Hide the hamburger menu */
    .stApp > div[data-testid="stSidebar"] > div[data-testid="stSidebarUserContent"] > div[data-testid="stSidebarNav"] > div[data-testid="stSidebarNavItems"] > div[data-testid="stSidebarNavLink"]:first-child {display:none;}
    
    /* Hide the top bar completely */
    .stApp > div[data-testid="stHeader"] {display:none;}
    
    /* Adjust main content padding */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .page-header {
        background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .page-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .page-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .login-form {
        margin-bottom: 1.5rem;
    }
    
    .login-button {
        width: 100%;
        background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        font-weight: 500;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(139, 92, 246, 0.4);
    }
    
    .register-link {
        text-align: center;
        margin-top: 1rem;
    }
    
    .register-link a {
        color: #8B5CF6;
        text-decoration: none;
        font-weight: 500;
    }
    
    .register-link a:hover {
        text-decoration: underline;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #f5c6cb;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #c3e6cb;
    }
    
    .form-group {
        margin-bottom: 1rem;
    }
    
    .form-label {
        display: block;
        margin-bottom: 0.5rem;
        font-weight: 500;
        color: #333;
    }
    
    .form-input {
        width: 100%;
        padding: 0.75rem;
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .form-input:focus {
        outline: none;
        border-color: #8B5CF6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🔐 로그인</div>
        <div class="page-subtitle">HAI Portal에 로그인하여 AI 채팅 서비스를 이용하세요</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "login_mode" not in st.session_state:
        st.session_state.login_mode = "login"
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    
    # Check if user is already logged in
    if st.session_state.get("auth_token") and st.session_state.get("user_info"):
        st.success("이미 로그인되어 있습니다.")
        if st.button("메인 페이지로 이동"):
            st.session_state.current_page = "main"
            st.rerun()
        return
    
    # Main container
    st.markdown("""
    <div class="login-container">
        <div class="login-header">
            <div class="login-title">HAI Portal</div>
            <div class="login-subtitle">AI 기반 지능형 서비스 플랫폼</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Login/Register form
    if st.session_state.login_mode == "login":
        st.markdown("### 🔐 로그인")
        
        with st.form("login_form"):
            username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_submitted = st.form_submit_button("로그인", use_container_width=True)
            with col2:
                register_switch = st.form_submit_button("회원가입", use_container_width=True)
        
        if login_submitted:
            if not username or not password:
                st.error("사용자명과 비밀번호를 모두 입력해주세요.")
            else:
                with st.spinner("로그인 중..."):
                    result = login_user(username, password)
                
                if result.get("success"):
                    # Store authentication info
                    st.session_state.auth_token = result.get("access_token")
                    st.session_state.user_info = result.get("user")
                    st.session_state.refresh_token = result.get("refresh_token")
                    
                    # Store in session storage for persistence
                    st.session_state.login_time = datetime.now().isoformat()
                    
                    st.success("로그인에 성공했습니다!")
                    st.session_state.current_page = "main"
                    st.rerun()
                else:
                    st.error(result.get("message", "로그인에 실패했습니다."))
        
        if register_switch:
            st.session_state.login_mode = "register"
            st.rerun()
    
    else:  # register mode
        st.markdown("### 📝 회원가입")
        
        with st.form("register_form"):
            username = st.text_input("사용자명", placeholder="3자 이상 입력하세요")
            email = st.text_input("이메일", placeholder="이메일 주소를 입력하세요")
            password = st.text_input("비밀번호", type="password", placeholder="6자 이상 입력하세요")
            confirm_password = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력하세요")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                register_submitted = st.form_submit_button("회원가입", use_container_width=True)
            with col2:
                login_switch = st.form_submit_button("로그인", use_container_width=True)
        
        if register_submitted:
            if not all([username, email, password, confirm_password]):
                st.error("모든 필드를 입력해주세요.")
            elif len(username) < 3:
                st.error("사용자명은 3자 이상이어야 합니다.")
            elif len(password) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            elif password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
            elif "@" not in email:
                st.error("유효한 이메일 주소를 입력해주세요.")
            else:
                with st.spinner("회원가입 중..."):
                    result = register_user(username, email, password, confirm_password)
                
                if result.get("success"):
                    st.success("회원가입이 완료되었습니다! 로그인해주세요.")
                    st.session_state.login_mode = "login"
                    st.rerun()
                else:
                    st.error(result.get("message", "회원가입에 실패했습니다."))
        
        if login_switch:
            st.session_state.login_mode = "login"
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        HAI Portal v1.0.0 | AI 기반 지능형 서비스 플랫폼
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
