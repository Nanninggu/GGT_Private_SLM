"""
Login page for HAI Portal
"""
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="로그인",
    page_icon="🔐",
    layout="wide"
)
import requests
import json
import sys
import os
from datetime import datetime, timedelta

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_service import APIService
from utils.session_manager import session_manager

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
    
    # Modern Enterprise UI - Pure White Login Theme
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
    
    /* Global styling - Pure White Background */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Adjust main content padding */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        background-color: #ffffff;
    }
    
    /* Modern Enterprise page header - Clean White Design */
    .page-header {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        margin-bottom: 3rem;
        color: #212529;
        text-align: center;
        box-shadow: 0 8px 40px rgba(0,0,0,0.06);
        border: 2px solid #f1f3f4;
        position: relative;
        overflow: hidden;
    }
    
    .page-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6c757d 0%, #495057 50%, #6c757d 100%);
    }
    
    .page-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.75rem;
        letter-spacing: -0.03em;
        color: #212529;
        text-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .page-subtitle {
        font-size: 1.3rem;
        opacity: 0.8;
        font-weight: 500;
        color: #6c757d;
    }
    
    /* Modern Enterprise login container - Pure White */
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 4rem;
        background: #ffffff;
        border-radius: 28px;
        box-shadow: 0 12px 48px rgba(0,0,0,0.08);
        border: 2px solid #f1f3f4;
        position: relative;
        overflow: hidden;
    }
    
    .login-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
    }
    
    .login-form {
        margin-bottom: 2.5rem;
    }
    
    /* Modern Enterprise button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        color: #495057;
        border: 2px solid #e9ecef;
        padding: 1.25rem 2rem;
        border-radius: 16px;
        font-weight: 700;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        text-transform: none;
        letter-spacing: 0.01em;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.15);
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-color: #6c757d;
        color: #212529;
    }
    
    .register-link {
        text-align: center;
        margin-top: 2rem;
    }
    
    .register-link a {
        color: #6c757d;
        text-decoration: none;
        font-weight: 600;
        transition: color 0.3s ease;
        font-size: 1rem;
    }
    
    .register-link a:hover {
        color: #495057;
        text-decoration: underline;
    }
    
    /* Modern Enterprise form styling */
    .stTextInput > div > div > input {
        border-radius: 16px;
        border: 2px solid #f1f3f4;
        padding: 1.25rem 1.5rem;
        font-size: 1.1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        background: #ffffff;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6c757d;
        box-shadow: 0 0 0 4px rgba(108, 117, 125, 0.1);
        outline: none;
        background: #ffffff;
    }
    
    /* Modern Enterprise error/success messages */
    .stAlert {
        border-radius: 16px;
        border: 2px solid;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        background: #ffffff;
    }
    
    .stAlert[data-testid="alert"] {
        background: #ffffff;
    }
    
    /* Modern Enterprise form labels */
    .stTextInput > label {
        font-weight: 700;
        color: #212529;
        margin-bottom: 0.75rem;
        font-size: 1rem;
    }
    
    /* Modern Enterprise radio button styling */
    .stRadio > div {
        gap: 1.5rem;
    }
    
    .stRadio > div > label {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 16px;
        border: 2px solid #f1f3f4;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    
    .stRadio > div > label:hover {
        border-color: #6c757d;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        background: #f8f9fa;
    }
    
    /* Modern Enterprise selectbox styling */
    .stSelectbox > div > div {
        border-radius: 16px;
        border: 2px solid #f1f3f4;
        background: #ffffff;
    }
    
    /* Modern Enterprise checkbox styling */
    .stCheckbox > label {
        font-weight: 600;
        color: #212529;
        font-size: 1rem;
    }
    
    /* Form section styling */
    .form-section {
        background: #ffffff;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 2px solid #f1f3f4;
        margin-bottom: 2rem;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .login-container {
            padding: 3rem 2rem;
            margin: 1rem;
        }
        
        .page-header {
            padding: 3rem 1.5rem;
        }
        
        .page-title {
            font-size: 2.5rem;
        }
        
        .form-section {
            padding: 2rem 1.5rem;
        }
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
    
    # Initialize session state with persistent session manager
    session_manager.initialize_session()
    
    # Initialize other session state
    if "login_mode" not in st.session_state:
        st.session_state.login_mode = "login"
    
    # Check if user is already logged in with auto token refresh
    if st.session_state.get("auth_token") and st.session_state.get("user_info"):
        # Check if token needs refresh
        login_time = st.session_state.get("login_time")
        if login_time:
            try:
                login_datetime = datetime.fromisoformat(login_time)
                # Check if more than 7 hours have passed (8 hours - 1 hour buffer)
                if datetime.now() - login_datetime > timedelta(hours=7):
                    # Try to refresh token
                    refresh_token = st.session_state.get("refresh_token")
                    if refresh_token:
                        try:
                            from services.api_service import APIService
                            api_service = APIService()
                            result = api_service.refresh_token(refresh_token)
                            if result.get("success"):
                                st.session_state.auth_token = result.get("access_token")
                                st.session_state.refresh_token = result.get("refresh_token")
                                st.session_state.login_time = datetime.now().isoformat()
                                # Update user info if available
                                if result.get("user"):
                                    st.session_state.user_info = result.get("user")
                                st.success("세션이 자동으로 갱신되었습니다.")
                            else:
                                # If refresh fails, clear session
                                st.session_state.auth_token = None
                                st.session_state.user_info = None
                                st.session_state.refresh_token = None
                                st.session_state.login_time = None
                                st.warning("세션이 만료되었습니다. 다시 로그인해주세요.")
                                return
                        except:
                            st.warning("세션 갱신 중 오류가 발생했습니다. 다시 로그인해주세요.")
                            return
            except:
                pass
        
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
                    st.session_state.login_time = datetime.now().isoformat()
                    
                    # Save session to persistent storage
                    session_manager.save_current_session()
                    
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
                    # Store authentication info for auto-login after registration
                    st.session_state.auth_token = result.get("access_token")
                    st.session_state.user_info = result.get("user")
                    st.session_state.refresh_token = result.get("refresh_token")
                    st.session_state.login_time = datetime.now().isoformat()
                    
                    # Save session to persistent storage
                    session_manager.save_current_session()
                    
                    st.success("회원가입이 완료되었습니다! 자동으로 로그인됩니다.")
                    st.session_state.current_page = "main"
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
