"""
Main Streamlit application for Exaone chatbot
"""
import streamlit as st
import sys
import os
import uuid
from datetime import datetime, timedelta

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.chat_controller import ChatController
from components.chat_components import ChatComponents, StatusComponents
from config import ADMIN_USER_ID
from utils.session_manager import session_manager
from services.session_management_service import session_manager as new_session_manager
from services.sidebar_management_service import sidebar_manager
from utils.auth_persistence import AuthPersistence

# Set page configuration once at the top
st.set_page_config(
    page_title="채팅",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_auth_status():
    """Check if user is authenticated with auto token refresh and persistence"""
    # 먼저 session_state에서 인증 토큰 확인
    if not st.session_state.get("auth_token"):
        # session_state에 토큰이 없으면 영구 저장된 인증 상태 복원 시도
        auth_data = AuthPersistence.load_auth_state()
        if auth_data:
            # 토큰 만료 확인
            if not AuthPersistence.is_token_expired(auth_data.get("login_time", "")):
                # 토큰이 유효하면 session_state에 복원
                AuthPersistence.restore_auth_to_session(auth_data)
            else:
                # 토큰이 만료되었으면 refresh 시도
                refresh_token = auth_data.get("refresh_token")
                if refresh_token:
                    try:
                        from services.api_service import APIService
                        api_service = APIService()
                        result = api_service.refresh_token(refresh_token)
                        if result.get("success"):
                            # 새로운 토큰으로 인증 상태 업데이트
                            AuthPersistence.save_auth_state(
                                result.get("access_token"),
                                result.get("refresh_token"),
                                result.get("user", auth_data.get("user_info", {})),
                                datetime.now().isoformat()
                            )
                        else:
                            # refresh 실패 시 저장된 인증 상태 삭제
                            AuthPersistence.clear_auth_state()
                            return False
                    except:
                        AuthPersistence.clear_auth_state()
                        return False
                else:
                    AuthPersistence.clear_auth_state()
                    return False
        else:
            return False
    
    # Check if token is expired based on login time
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
                            return True
                    except:
                        pass
                # If refresh fails, clear session
                st.session_state.auth_token = None
                st.session_state.user_info = None
                st.session_state.refresh_token = None
                st.session_state.login_time = None
                return False
        except:
            pass
    
    # Verify token with backend
    try:
        from services.api_service import APIService
        api_service = APIService()
        result = api_service.verify_token(st.session_state.auth_token)
        return result.get("valid", False)
    except:
        return False

def main():
    """Main application function"""
    # Initialize session state with persistent session manager
    session_manager.initialize_session()
    
    # 새로고침 시 인증 상태 자동 복원
    if not st.session_state.get("auth_token") and not st.session_state.get("auth_restored"):
        auth_data = AuthPersistence.load_auth_state()
        if auth_data:
            # 토큰 만료 확인
            if not AuthPersistence.is_token_expired(auth_data.get("login_time", "")):
                # 토큰이 유효하면 session_state에 복원
                AuthPersistence.restore_auth_to_session(auth_data)
                st.session_state.auth_restored = True
                st.rerun()  # 복원 후 페이지 새로고침
            else:
                # 토큰이 만료되었으면 refresh 시도
                refresh_token = auth_data.get("refresh_token")
                if refresh_token:
                    try:
                        from services.api_service import APIService
                        api_service = APIService()
                        result = api_service.refresh_token(refresh_token)
                        if result.get("success"):
                            # 새로운 토큰으로 인증 상태 업데이트
                            AuthPersistence.save_auth_state(
                                result.get("access_token"),
                                result.get("refresh_token"),
                                result.get("user", auth_data.get("user_info", {})),
                                datetime.now().isoformat()
                            )
                            st.session_state.auth_restored = True
                            st.rerun()
                        else:
                            # refresh 실패 시 저장된 인증 상태 삭제
                            AuthPersistence.clear_auth_state()
                    except:
                        AuthPersistence.clear_auth_state()
                else:
                    AuthPersistence.clear_auth_state()
    
    # Initialize other session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = "default"
    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = False
    if "last_loaded_session" not in st.session_state:
        st.session_state.last_loaded_session = None
    if "force_refresh" not in st.session_state:
        st.session_state.force_refresh = False
    if "is_new_session" not in st.session_state:
        st.session_state.is_new_session = False
    if "current_page" not in st.session_state:
        st.session_state.current_page = "main"
    if "last_page" not in st.session_state:
        st.session_state.last_page = "main"
    
    # Handle new chat creation flag (legacy support)
    if st.session_state.get("create_new_chat", False):
        # This is now handled directly in the sidebar component
        # Clear the flag to prevent duplicate processing
        st.session_state.create_new_chat = False
    
    # Page routing
    current_page = st.session_state.current_page
    last_page = st.session_state.last_page
    
    # Update last page if current page changed
    if current_page != last_page:
        st.session_state.last_page = current_page
    
    # Route to different pages without calling st.set_page_config
    if current_page == "login":
        from pages.login import main as login_main
        login_main()
        return
    elif current_page == "file_upload":
        from pages.file_upload import main as file_upload_main
        file_upload_main()
        return
    elif current_page == "accessibility_demo":
        from pages.accessibility_demo import main as accessibility_main
        accessibility_main()
        return
    elif current_page == "configuration":
        from pages.configuration import main as configuration_main
        configuration_main()
        return
    elif current_page == "user_management":
        from pages.user_management import main as user_management_main
        user_management_main()
        return
    elif current_page == "menu_management":
        from pages.menu_management import main as menu_management_main
        menu_management_main()
        return
    elif current_page == "session_management":
        from pages.session_management import main as session_management_main
        session_management_main()
        return
    elif current_page == "main":
        # Main page - continue with main page logic
        pass
    else:
        # Default to main page
        st.session_state.current_page = "main"
        # Don't rerun here to avoid infinite loop
    
    # Check authentication for main page
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # Initialize user session if not already initialized
    user_info = st.session_state.get("user_info", {})
    user_id = user_info.get("id", "default")
    
    # Check for user change and save previous user's session
    previous_user_id = st.session_state.get("current_user_id")
    if previous_user_id and previous_user_id != user_id and new_session_manager:
        # Save previous user's session before switching
        if st.session_state.get("messages"):
            new_session_manager.save_current_session(previous_user_id)
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - Saved previous user {previous_user_id} session before switching to {user_id}")
    
    if new_session_manager and user_id != "default":
        # Check if user session is initialized
        if "user_sessions" not in st.session_state or user_id not in st.session_state.user_sessions:
            new_session_manager.initialize_user_session(user_id, user_info)
            if st.session_state.get("debug_mode", False):
                st.write(f"🔍 Debug - Initialized new user session for {user_id}")
    
    # Update current user ID
    st.session_state.current_user_id = user_id
    
    # Save current session periodically
    if st.session_state.get("auth_token"):
        if new_session_manager and user_id != "default":
            new_session_manager.save_current_session(user_id)
        else:
            # Fallback to old session management
            session_manager.save_current_session()
        
        # Also save chat session to backend
        if st.session_state.backend_connected and st.session_state.get("messages"):
            try:
                chat_controller = ChatController()
                chat_controller.save_current_session()
            except:
                pass  # Continue even if save fails

    # Initialize controller
    chat_controller = ChatController()

    # Check backend connection only once
    if not st.session_state.backend_connected:
        st.session_state.backend_connected = chat_controller.check_backend_connection()
    
    # Handle force refresh after session deletion
    if st.session_state.get("force_refresh", False):
        st.session_state.force_refresh = False
        st.session_state.last_loaded_session = None  # Reset to force reload
        st.rerun()
    
    # Load chat history if session changed or if this is a page refresh
    current_session = st.session_state.session_id
    should_load_history = (
        current_session != st.session_state.last_loaded_session or 
        (st.session_state.backend_connected and len(st.session_state.messages) == 0)
    )
    
    # Debug logging
    if st.session_state.get("debug_mode", False):
        st.write(f"🔍 Debug - Current session: {current_session}")
        st.write(f"🔍 Debug - Last loaded session: {st.session_state.last_loaded_session}")
        st.write(f"🔍 Debug - Should load history: {should_load_history}")
        st.write(f"🔍 Debug - Backend connected: {st.session_state.backend_connected}")
        st.write(f"🔍 Debug - Messages count: {len(st.session_state.messages)}")
    
    if should_load_history and st.session_state.backend_connected:
        # Skip existence check for new sessions to avoid unnecessary API calls
        if st.session_state.get("is_new_session", False):
            # New session - just update last_loaded_session without checking existence
            st.session_state.last_loaded_session = current_session
            # Don't reset flag here - let sidebar handle it to avoid re-fetching sessions
        else:
            # Existing session - check if it exists and load history if it does
            if current_session == "default" or chat_controller.check_session_exists(current_session):
                if st.session_state.get("debug_mode", False):
                    st.write(f"🔍 Debug - Loading history for session: {current_session}")
                chat_controller.load_session_history(current_session)
                st.session_state.last_loaded_session = current_session
            else:
                # Session doesn't exist - just update last_loaded_session
                if st.session_state.get("debug_mode", False):
                    st.write(f"🔍 Debug - Session {current_session} does not exist")
                st.session_state.last_loaded_session = current_session

    # Render dynamic sidebar navigation
    sidebar_manager.render_sidebar()
    
    # Render chat sidebar (for session management)
    sidebar_action = ChatComponents.render_sidebar()

    # Handle sidebar actions
    if sidebar_action == "clear_chat":
        st.session_state.messages = []
    elif sidebar_action == "logout":
        # Use new session management service if available
        user_info = st.session_state.get("user_info", {})
        user_id = user_info.get("id", "default")
        
        # 현재 사용자의 세션 저장
        if new_session_manager and user_id != "default":
            # 현재 메시지가 있으면 저장
            if st.session_state.get("messages"):
                new_session_manager.save_current_session(user_id)
            new_session_manager.logout_user(user_id)
        else:
            # Fallback to old session management
            session_manager.save_current_session()
            session_manager.clear_session()
        
        # 영구 저장된 인증 상태도 삭제
        AuthPersistence.clear_auth_state()
        
        # 인증 복원 플래그 초기화
        if "auth_restored" in st.session_state:
            del st.session_state.auth_restored
        
        st.session_state.messages = []
        st.session_state.current_page = "login"
        st.success("로그아웃되었습니다.")
        st.rerun()
    elif sidebar_action == "check_connection":
        st.session_state.backend_connected = chat_controller.check_backend_connection()
        if st.session_state.backend_connected:
            StatusComponents.show_success("백엔드 서버에 연결되었습니다.")
        else:
            StatusComponents.show_error("백엔드 서버에 연결할 수 없습니다.")

    # Inject accessibility scripts
    ChatComponents._inject_accessibility_scripts()

    # Hide Streamlit default header elements
    from utils.helpers import UIHelpers
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

    # Main header - removed HAI Portal content
    
    # Service cards - removed HAI-Chat content
    
    # Welcome message with modern styling
    st.markdown("""
    <div style="text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                border-radius: 20px; margin: 2rem 0; border: 2px solid #e9ecef; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🤖</div>
        <h3 style="color: #495057; margin-bottom: 1rem; font-weight: 600;">AI 챗봇에 오신 것을 환영합니다!</h3>
        <p style="color: #6c757d; font-size: 1.1rem; margin-bottom: 1.5rem; line-height: 1.6;">
            AI와 대화하고 문서를 분석해보세요.<br>
            아래에 메시지를 입력하여 시작하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat interface section
    st.markdown("---")
    
    # Chat header
    st.markdown("### 💬 AI 챗봇 대화")
    
    # Display chat history
    if st.session_state.messages:
        for message in st.session_state.messages:
            ChatComponents.render_message(message)
    else:
        # Show feature cards for new chat
        st.markdown("#### 🚀 사용 가능한 기능")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #e9ecef;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
                <div style="font-weight: 600; color: #495057; margin-bottom: 0.25rem;">일반 대화</div>
                <div style="font-size: 0.9rem; color: #6c757d;">AI와 자유롭게 대화하세요</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #e9ecef;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📚</div>
                <div style="font-weight: 600; color: #495057; margin-bottom: 0.25rem;">문서 분석</div>
                <div style="font-size: 0.9rem; color: #6c757d;">업로드한 문서를 분석해보세요</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #e9ecef;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
                <div style="font-weight: 600; color: #495057; margin-bottom: 0.25rem;">웹 검색</div>
                <div style="font-size: 0.9rem; color: #6c757d;">실시간 정보를 검색해보세요</div>
            </div>
            """, unsafe_allow_html=True)
    

    # Model selection section
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Model selection UI
    ChatComponents.render_model_selection()
    
    # Add spacing before chat input
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("HAI-Chat에게 메시지를 입력하세요..."):
        # Add user message to chat history
        user_message = {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # Update session title if this is the first user message
        if len(st.session_state.messages) == 1 and st.session_state.get("is_new_session", False):
            # This is the first message in a new session, generate title based on the question
            try:
                if chat_controller.api_service:
                    # Generate title using the backend API
                    title_response = chat_controller.api_service.generate_session_title(
                        st.session_state.session_id,
                        prompt,
                        st.session_state.get("user_id", "default")
                    )
                    
                    if title_response.get("success"):
                        st.session_state.session_title = title_response.get("title", f"새 대화 ({datetime.now().strftime('%m/%d %H:%M')})")
                    else:
                        # Fallback to simple title generation
                        clean_prompt = prompt.strip()
                        clean_prompt = clean_prompt.replace("질문:", "").replace("문의:", "").replace("요청:", "").strip()
                        
                        if len(clean_prompt) > 30:
                            clean_prompt = clean_prompt[:30] + "..."
                        
                        timestamp = datetime.now().strftime("%m/%d %H:%M")
                        st.session_state.session_title = f"💬 {clean_prompt} ({timestamp})"
                else:
                    # Fallback if API service is not available
                    clean_prompt = prompt.strip()
                    clean_prompt = clean_prompt.replace("질문:", "").replace("문의:", "").replace("요청:", "").strip()
                    
                    if len(clean_prompt) > 30:
                        clean_prompt = clean_prompt[:30] + "..."
                    
                    timestamp = datetime.now().strftime("%m/%d %H:%M")
                    st.session_state.session_title = f"💬 {clean_prompt} ({timestamp})"
                    
            except Exception as e:
                # Fallback in case of any error
                clean_prompt = prompt.strip()
                clean_prompt = clean_prompt.replace("질문:", "").replace("문의:", "").replace("요청:", "").strip()
                
                if len(clean_prompt) > 30:
                    clean_prompt = clean_prompt[:30] + "..."
                
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                st.session_state.session_title = f"💬 {clean_prompt} ({timestamp})"
            
            st.session_state.is_new_session = False
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Save user message to backend
        if st.session_state.backend_connected:
            try:
                chat_controller.api_service.save_message(user_message, st.session_state.session_id)
            except Exception as e:
                st.error(f"메시지 저장 실패: {e}")
        
        # Send message to backend and get response
        if st.session_state.backend_connected:
            try:
                # Check if streaming is enabled
                streaming_enabled = st.session_state.get("streaming_enabled", True)
                
                # Get selected model type
                selected_model_type = st.session_state.get("selected_model_type", "fast")
                
                if streaming_enabled:
                    # Use streaming response with enhanced loading
                    rag_mode = st.session_state.get("rag_mode", "LangChain RAG")
                    with st.spinner(f"🤖 {rag_mode}로 답변을 생성하고 있습니다..."):
                        response = chat_controller.send_message_stream(prompt, selected_model_type)
                else:
                    # Use regular response with enhanced spinner
                    rag_mode = st.session_state.get("rag_mode", "LangChain RAG")
                    
                    # Generate response with spinner
                    if rag_mode == "LangChain RAG":
                        with st.spinner("🤖 LangChain RAG로 답변을 생성하고 있습니다..."):
                            response = chat_controller.send_message_langchain(prompt, selected_model_type)
                    else:
                        with st.spinner("🤖 RAG로 답변을 생성하고 있습니다..."):
                            response = chat_controller.send_message(prompt, selected_model_type)
                
                if response:
                    # Handle different response types
                    if isinstance(response, dict):
                        # Response with context information
                        assistant_message = {
                            "id": str(uuid.uuid4()),
                            "role": "assistant",
                            "content": response.get("content", ""),
                            "context": response.get("context", []),
                            "metadata": response.get("metadata", {}),
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        }
                    else:
                        # Simple string response
                        assistant_message = {
                            "id": str(uuid.uuid4()),
                            "role": "assistant",
                            "content": response,
                            "context": [],
                            "metadata": {},
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        }
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append(assistant_message)
                    
                    # Save assistant message to backend
                    if st.session_state.backend_connected:
                        try:
                            chat_controller.api_service.save_message(assistant_message, st.session_state.session_id)
                        except Exception as e:
                            st.error(f"응답 저장 실패: {e}")
                    
                    # Display assistant response (only for non-streaming)
                    if not streaming_enabled:
                        ChatComponents.render_message(assistant_message)
                        
                        # Show collection information
                        metadata = assistant_message.get("metadata", {})
                        if metadata.get("multi_collection", False):
                            collections_used = metadata.get("collections_used", [])
                            if collections_used:
                                st.info(f"🔍 검색된 컬렉션: {', '.join(collections_used)}")
                        
                        # Show RAG mode indicator
                        if rag_mode == "LangChain RAG":
                            st.caption("🧠 LangChain RAG 모드")
                        else:
                            st.caption("⚡ 기본 RAG 모드")
                else:
                    st.error("응답을 받을 수 없습니다.")
            except Exception as e:
                st.error(f"메시지 전송 중 오류가 발생했습니다: {str(e)}")
        else:
            st.error("백엔드 서버에 연결할 수 없습니다.")

if __name__ == "__main__":
    main()
