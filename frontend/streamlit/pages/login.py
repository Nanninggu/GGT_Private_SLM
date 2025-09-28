"""
Login page
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
from services.session_management_service import session_manager
from utils.helpers import UIHelpers, SessionManager

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
    
    # Hide Streamlit default header elements
    UIHelpers.hide_streamlit_header()
    
    # Apply Material Design 3 Theme
    from utils.helpers import DesignThemeManager
    theme_manager = DesignThemeManager()
    
    # Load theme from file if not already loaded
    if "theme_loaded" not in st.session_state:
        try:
            import json
            with open("data/theme_settings.json", "r", encoding="utf-8") as f:
                theme_settings = json.load(f)
                st.session_state.selected_theme = theme_settings.get("selected_theme", "gemini")
                st.session_state.theme_loaded = True
        except:
            st.session_state.selected_theme = "gemini"
            st.session_state.theme_loaded = True
    
    # Get theme from session state or default to gemini
    selected_theme = st.session_state.get("selected_theme", "gemini")
    theme_manager.apply_theme(selected_theme)
    
    # Check if redirected from session expiry
    session_expired = st.session_state.get("session_expired", False)
    
    # Page header
    if session_expired:
        st.markdown("""
        <div class="page-header">
            <div class="page-title">🔒 세션 만료</div>
            <div class="page-subtitle">세션이 만료되었습니다. 다시 로그인해주세요</div>
        </div>
        """, unsafe_allow_html=True)
        st.error("🔒 세션이 만료되었습니다. 보안을 위해 다시 로그인해주세요.")
    else:
        st.markdown("""
        <div class="page-header">
            <div class="page-title">🔐 로그인</div>
            <div class="page-subtitle">AI 채팅 서비스를 이용하세요</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize session state with persistent session manager
    SessionManager.initialize_session()
    
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
                    # Store authentication info in session_state
                    st.session_state.auth_token = result.get("access_token")
                    st.session_state.user_info = result.get("user")
                    st.session_state.refresh_token = result.get("refresh_token")
                    st.session_state.login_time = datetime.now().isoformat()
                    
                    # 영구 저장을 위한 인증 상태 저장
                    from utils.auth_persistence import AuthPersistence
                    AuthPersistence.save_auth_state(
                        result.get("access_token"),
                        result.get("refresh_token"),
                        result.get("user"),
                        datetime.now().isoformat()
                    )
                    
                    # Clear any session expiry flags
                    if "session_expired" in st.session_state:
                        del st.session_state.session_expired
                    
                    # Initialize user session with new session management service
                    user_info = result.get("user")
                    user_id = user_info.get("id", "default")
                    
                    if session_manager and user_id != "default":
                        session_manager.initialize_user_session(user_id, user_info)
                        st.success("로그인에 성공했습니다! 사용자별 세션이 초기화되었습니다.")
                    else:
                        # Fallback to old session management
                        try:
                            SessionManager.save_current_session()
                        except Exception as e:
                            print(f"세션 저장 중 오류 (무시됨): {e}")
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
                    
                    # Initialize user session with new session management service
                    user_info = result.get("user")
                    user_id = user_info.get("id", "default")
                    
                    if session_manager and user_id != "default":
                        session_manager.initialize_user_session(user_id, user_info)
                        st.success("회원가입이 완료되었습니다! 사용자별 세션이 초기화되었습니다.")
                    else:
                        # Fallback to old session management
                        try:
                            SessionManager.save_current_session()
                        except Exception as e:
                            print(f"세션 저장 중 오류 (무시됨): {e}")
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
        AI 채팅 서비스 v1.0.0
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
