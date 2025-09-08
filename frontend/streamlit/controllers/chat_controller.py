"""
Chat controller for managing chat functionality in Streamlit
"""
import streamlit as st
from typing import Dict, Any, List, Optional
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_service import APIService
import uuid
from datetime import datetime

class ChatController:
    """Controller for chat-related functionality"""

    def __init__(self):
        self.api_service = APIService()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state"""
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "backend_connected" not in st.session_state:
            st.session_state.backend_connected = False

    def check_backend_connection(self) -> bool:
        """Check if backend is connected"""
        connected = self.api_service.health_check()
        st.session_state.backend_connected = connected
        return connected

    def send_message(self, message: str) -> Optional[str]:
        """Send a message and return response content"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        # Check backend connection
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Send message to backend
        with st.spinner("응답을 생성하고 있습니다..."):
                    response = self.api_service.send_message(message, st.session_state.session_id, use_rag=True)

        if response["success"]:
            return response["assistant_message"]["content"]
        else:
            st.error(f"오류가 발생했습니다: {response.get('error', '알 수 없는 오류')}")
            return None

    def clear_chat(self):
        """Clear current chat session"""
        if st.session_state.backend_connected:
            self.api_service.clear_session(st.session_state.session_id)

        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.success("채팅이 초기화되었습니다.")

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get current chat history"""
        return st.session_state.messages

    def load_session_history(self, session_id: str):
        """Load chat history from backend"""
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다.")
            return

        response = self.api_service.get_chat_history(session_id)
        if response["success"]:
            st.session_state.messages = response["messages"]
            st.session_state.session_id = session_id
            st.success("채팅 기록을 불러왔습니다.")
        else:
            st.error(f"채팅 기록을 불러올 수 없습니다: {response.get('error', '알 수 없는 오류')}")

    def get_available_sessions(self) -> List[str]:
        """Get list of available sessions"""
        if not self.check_backend_connection():
            return []

        response = self.api_service.get_sessions()
        if response["success"]:
            return response["sessions"]
        return []
    
    def send_message_langchain(self, message: str, use_rag: bool = True) -> Optional[str]:
        """Send a message using LangChain RAG"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        # Check backend connection
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Send message to backend using LangChain
        with st.spinner("LangChain RAG로 응답을 생성하고 있습니다..."):
            response = self.api_service.send_message_langchain(message, st.session_state.session_id, use_rag)

        if response["success"]:
            return response["assistant_message"]["content"]
        else:
            st.error(f"LangChain RAG 오류가 발생했습니다: {response.get('error', '알 수 없는 오류')}")
            return None
    
    def send_message_stream(self, message: str, use_rag: bool = True) -> Optional[str]:
        """Send message with streaming response"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None

        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None

        # Create message container for streaming
        message_container = st.empty()
        full_response = ""
        context_sources = []
        
        try:
            # Get streaming response
            rag_mode = st.session_state.get("rag_mode", "기본 RAG")
            use_langchain = (rag_mode == "LangChain RAG")
            
            for chunk in self.api_service.send_message_stream(message, st.session_state.session_id, use_langchain):
                if "error" in chunk:
                    st.error(f"스트리밍 오류: {chunk['error']}")
                    return None
                
                if chunk.get("type") == "context":
                    context_sources = chunk.get("sources", [])
                    if context_sources:
                        with message_container.container():
                            st.info(f"📚 참고 문서: {', '.join(context_sources)}")
                
                if chunk.get("content"):
                    full_response += chunk["content"]
                    with message_container.container():
                        st.markdown(full_response + "▌")  # Cursor effect
                
                if chunk.get("finished", False):
                    break
            
            # Final response without cursor
            with message_container.container():
                st.markdown(full_response)
            
            return full_response
            
        except Exception as e:
            st.error(f"스트리밍 메시지 전송 중 오류가 발생했습니다: {str(e)}")
            return None
