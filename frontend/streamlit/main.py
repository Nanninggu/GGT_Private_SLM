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
    page_title="Exaone 챗봇",
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
        st.session_state.session_id = "default_session"
    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = False

    # Initialize controller
    chat_controller = ChatController()

    # Check backend connection only once
    if not st.session_state.backend_connected:
        st.session_state.backend_connected = chat_controller.check_backend_connection()

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

    # Main chat interface
    st.title("🤖 Exaone 3.5 2.4 챗봇")
    st.markdown("로컬 SLM 모델을 사용한 AI 챗봇과 대화해보세요!")
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("📁 파일 업로드", use_container_width=True):
            st.switch_page("pages/file_upload.py")
    with col2:
        if st.button("🗂️ 컬렉션 관리", use_container_width=True):
            st.switch_page("pages/collection_management.py")
    with col3:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()

    # Show connection status
    StatusComponents.show_connection_status(st.session_state.backend_connected)

    # Display chat history
    for message in st.session_state.messages:
        ChatComponents.render_message(message)

    # Chat input
    if prompt := st.chat_input("메시지를 입력하세요..."):
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
                    # Use streaming response
                    response = chat_controller.send_message_stream(prompt)
                else:
                    # Use regular response
                    with st.spinner("응답을 생성하고 있습니다..."):
                        rag_mode = st.session_state.get("rag_mode", "기본 RAG")
                        
                        if rag_mode == "LangChain RAG":
                            response = chat_controller.send_message_langchain(prompt)
                        else:
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
