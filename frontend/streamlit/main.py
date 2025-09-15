"""
Main Streamlit application for Exaone chatbot
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.chat_controller import ChatController
from components.chat_components import ChatComponents, StatusComponents

# Page configuration
st.set_page_config(
    page_title="HAI Portal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    # Service status and navigation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Service card
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">💬</div>
            <div class="service-title">HAI-Chat</div>
            <div class="service-description">AI 챗봇과 대화하고 문서를 분석해보세요</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Status and navigation
        st.markdown("### 🔧 서비스 관리")
        
        # Connection status
        if st.session_state.backend_connected:
            st.markdown('<div class="status-indicator status-online">🟢 서비스 온라인</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-indicator status-offline">🔴 서비스 오프라인</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation buttons
        if st.button("📁 파일 업로드", use_container_width=True):
            st.switch_page("pages/file_upload.py")
        if st.button("🗂️ 컬렉션 관리", use_container_width=True):
            st.switch_page("pages/collection_management.py")
        if st.button("♿ 접근성 데모", use_container_width=True):
            st.switch_page("pages/accessibility_demo.py")
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()

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
    

    # Add spacing before chat input
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("HAI-Chat에게 메시지를 입력하세요..."):
        # Add user message to chat history
        st.session_state.messages.append({
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
                
                if streaming_enabled:
                    # Use streaming response with enhanced loading
                    with st.spinner("🤖 AI가 답변을 생성하고 있습니다..."):
                        response = chat_controller.send_message_stream(prompt)
                else:
                    # Use regular response with enhanced spinner
                    rag_mode = st.session_state.get("rag_mode", "기본 RAG")
                    
                    # Generate response with spinner
                    if rag_mode == "LangChain RAG":
                        with st.spinner("🤖 LangChain RAG로 답변을 생성하고 있습니다..."):
                            response = chat_controller.send_message_langchain(prompt)
                    else:
                        with st.spinner("🤖 RAG로 답변을 생성하고 있습니다..."):
                            response = chat_controller.send_message(prompt)
                
                if response:
                    # Handle different response types
                    if isinstance(response, dict):
                        # Response with context information
                        assistant_message = {
                            "role": "assistant",
                            "content": response.get("content", ""),
                            "context": response.get("context", []),
                            "metadata": response.get("metadata", {}),
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        }
                    else:
                        # Simple string response
                        assistant_message = {
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
