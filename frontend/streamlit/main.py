"""
Main Streamlit application for Exaone chatbot
"""
import streamlit as st
import sys
import os
import uuid
from datetime import datetime

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.chat_controller import ChatController
from components.chat_components import ChatComponents, StatusComponents

# Page configuration will be set dynamically based on current page

def check_auth_status():
    """Check if user is authenticated"""
    if not st.session_state.get("auth_token"):
        return False
    
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
    # Initialize session state
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
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "main"
    
    # Page routing
    current_page = st.session_state.current_page
    
    # Set page configuration based on current page
    if current_page == "login":
        st.set_page_config(
            page_title="HAI Portal - 로그인",
            page_icon="🔐",
            layout="centered",
            initial_sidebar_state="collapsed"
        )
        from pages.login import main as login_main
        login_main()
        return
    elif current_page == "file_upload":
        st.set_page_config(
            page_title="HAI Portal - 파일 업로드",
            page_icon="📁",
            layout="wide"
        )
        from pages.file_upload import main as file_upload_main
        file_upload_main()
        return
    elif current_page == "accessibility_demo":
        st.set_page_config(
            page_title="접근성 데모 - HAI Portal",
            page_icon="♿",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        from pages.accessibility_demo import main as accessibility_main
        accessibility_main()
        return
    elif current_page == "configuration":
        st.set_page_config(
            page_title="시스템 설정 - HAI Portal",
            page_icon="⚙️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        from pages.configuration import main as configuration_main
        configuration_main()
        return
    elif current_page == "main":
        # Main page configuration
        st.set_page_config(
            page_title="HAI Portal",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    else:
        # Default configuration for main page
        st.set_page_config(
            page_title="HAI Portal",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    # Check authentication for main page
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return

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
    
    # Load chat history if session changed (but not for new sessions)
    current_session = st.session_state.session_id
    if (current_session != st.session_state.last_loaded_session and 
        st.session_state.backend_connected):
        
        # Skip existence check for new sessions to avoid unnecessary API calls
        if st.session_state.get("is_new_session", False):
            # New session - just update last_loaded_session without checking existence
            st.session_state.last_loaded_session = current_session
            # Don't reset flag here - let sidebar handle it to avoid re-fetching sessions
        else:
            # Existing session - check if it exists and load history if it does
            if current_session == "default" or chat_controller.check_session_exists(current_session):
                chat_controller.load_session_history(current_session)
                st.session_state.last_loaded_session = current_session
            else:
                # Session doesn't exist - just update last_loaded_session
                st.session_state.last_loaded_session = current_session

    # Render sidebar
    sidebar_action = ChatComponents.render_sidebar()

    # Handle sidebar actions
    if sidebar_action == "clear_chat":
        st.session_state.messages = []
        st.rerun()
    elif sidebar_action == "logout":
        # Clear authentication data
        st.session_state.auth_token = None
        st.session_state.user_info = None
        st.session_state.messages = []
        st.success("로그아웃되었습니다.")
        st.rerun()
    elif sidebar_action == "check_connection":
        st.session_state.backend_connected = chat_controller.check_backend_connection()
        if st.session_state.backend_connected:
            StatusComponents.show_success("백엔드 서버에 연결되었습니다.")
        else:
            StatusComponents.show_error("백엔드 서버에 연결할 수 없습니다.")
    elif isinstance(sidebar_action, tuple) and sidebar_action[0] == "download_pdf":
        # Handle PDF download
        pdf_type = sidebar_action[1]
        include_metadata = sidebar_action[2]
        
        if st.session_state.messages:
            try:
                from services.pdf_service import PDFService
                pdf_service = PDFService()
                
                # Get session info
                current_session = st.session_state.session_id
                session_name = st.session_state.get(f"session_name_{current_session}", "")
                
                # Generate PDF based on type
                if pdf_type == "전체 채팅 기록":
                    pdf_content = pdf_service.generate_chat_pdf(
                        st.session_state.messages,
                        current_session,
                        session_name,
                        include_metadata
                    )
                    filename = f"chat_history_{current_session}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                else:  # 요약 보고서
                    pdf_content = pdf_service.generate_summary_pdf(
                        st.session_state.messages,
                        current_session,
                        session_name
                    )
                    filename = f"chat_summary_{current_session}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Create download button
                st.download_button(
                    label=f"📥 {pdf_type} 다운로드",
                    data=pdf_content,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success(f"✅ {pdf_type} PDF가 생성되었습니다!")
                
            except Exception as e:
                st.error(f"❌ PDF 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("⚠️ 다운로드할 채팅 메시지가 없습니다.")
    elif isinstance(sidebar_action, tuple) and sidebar_action[0] == "download_markdown":
        # Handle Markdown download
        session_name = sidebar_action[1]
        include_metadata = sidebar_action[2]
        
        if st.session_state.messages:
            try:
                current_session = st.session_state.session_id
                
                # Export chat to markdown
                result = chat_controller.export_chat_markdown(
                    current_session, 
                    session_name, 
                    include_metadata
                )
                
                if result.get("success"):
                    filename = f"chat_history_{current_session}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    
                    st.download_button(
                        label="📥 마크다운 다운로드",
                        data=result.get("content", ""),
                        file_name=filename,
                        mime="text/markdown",
                        use_container_width=True
                    )
                    
                    st.success(f"✅ 마크다운 파일이 생성되었습니다!")
                    st.info(f"📊 총 {result.get('message_count', 0)}개의 메시지가 포함되었습니다.")
                else:
                    st.error(f"❌ 마크다운 생성 중 오류가 발생했습니다: {result.get('error', '알 수 없는 오류')}")
                
            except Exception as e:
                st.error(f"❌ 마크다운 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.warning("⚠️ 다운로드할 채팅 메시지가 없습니다.")

    # Inject accessibility scripts
    ChatComponents._inject_accessibility_scripts()

    # Custom CSS for HAI Portal styling
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
        padding-bottom: 2rem;
    }
    
    /* Chat message spacing */
    .stChatMessage {
        margin-bottom: 2rem !important;
    }
    
    /* Chat input spacing */
    .stChatInput {
        margin-top: 2rem !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    .service-card {
        background: white;
        padding: 3rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        text-align: center;
        margin: 2rem auto;
        max-width: 500px;
    }
    
    .service-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        color: #8B5CF6;
    }
    
    .service-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #333;
    }
    
    .service-description {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .status-online {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-offline {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .nav-button {
        background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        margin: 0.25rem;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(139, 92, 246, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

    # Main header
    st.markdown("""
    <div class="main-header">
        <div class="main-title">HAI Portal</div>
        <div class="main-subtitle">AI 기반 지능형 서비스 플랫폼</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Service card - centered
    st.markdown("""
    <div style="display: flex; justify-content: center; margin: 2rem 0;">
        <div class="service-card">
            <div class="service-icon">💬</div>
            <div class="service-title">HAI-Chat</div>
            <div class="service-description">AI 챗봇과 대화하고 문서를 분석해보세요</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chat interface section
    st.markdown("---")
    
    # Chat header with PDF download option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 💬 HAI-Chat 대화")
    with col2:
        if st.session_state.messages:
            if st.button("📄 전체 대화 PDF로 저장", key="download_all_chat"):
                try:
                    from services.pdf_service import PDFService
                    pdf_service = PDFService()
                    
                    current_session = st.session_state.session_id
                    session_name = st.session_state.get(f"session_name_{current_session}", "")
                    
                    pdf_content = pdf_service.generate_chat_pdf(
                        st.session_state.messages,
                        current_session,
                        session_name,
                        True
                    )
                    
                    filename = f"full_chat_{current_session}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    st.download_button(
                        label="📥 전체 대화 다운로드",
                        data=pdf_content,
                        file_name=filename,
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"PDF 생성 오류: {str(e)}")
    
    # Add spacing before chat messages
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.messages:
        ChatComponents.render_message(message)
    

    # Model selection section
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Model selection UI
    ChatComponents.render_model_selection()
    
    # Add spacing before chat input
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("HAI-Chat에게 메시지를 입력하세요..."):
        # Add user message to chat history
        st.session_state.messages.append({
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
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
                    
                    # Display assistant response (only for non-streaming)
                    if not streaming_enabled:
                        ChatComponents.render_message(assistant_message)
                        
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
