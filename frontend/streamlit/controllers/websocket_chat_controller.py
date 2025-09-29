"""
WebSocket chat controller for real-time chat functionality
"""
import asyncio
import streamlit as st
from typing import Dict, Any, Optional
import sys
import os
from datetime import datetime
import uuid

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.websocket_service import websocket_manager
from services.api_service import APIService

class WebSocketChatController:
    """Controller for WebSocket-based chat functionality"""
    
    def __init__(self):
        self.ws_service = None
        self.api_service = APIService(base_url="http://localhost:9502")
        self.is_connected = False
    
    def initialize_connection(self, session_id: str) -> bool:
        """Initialize WebSocket connection (synchronous wrapper)"""
        try:
            import asyncio
            
            # Create new event loop for this thread
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run async connection in the loop
            self.ws_service = websocket_manager.get_service(session_id)
            self.is_connected = loop.run_until_complete(self.ws_service.connect(session_id))
            
            if self.is_connected:
                st.success("✅ 실시간 채팅 연결이 활성화되었습니다.")
            else:
                st.warning("⚠️ 실시간 채팅 연결에 실패했습니다. HTTP 모드로 전환됩니다.")
            
            return self.is_connected
            
        except Exception as e:
            st.warning(f"⚠️ WebSocket 연결 오류: {str(e)}. HTTP 모드로 전환됩니다.")
            return False
    
    def check_backend_connection(self) -> bool:
        """Check if backend is running"""
        return self.api_service.health_check()
    
    def send_message_stream(self, message: str, model_type: str = "fast", use_rag: bool = True) -> Optional[str]:
        """Send message with WebSocket streaming response"""
        if not message.strip():
            st.error("메시지를 입력해주세요.")
            return None
        
        if not self.check_backend_connection():
            st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return None
        
        # Check and attempt to reconnect if needed
        if not self.is_connected or not self.ws_service:
            st.warning("⚠️ WebSocket 연결이 필요합니다. 재연결을 시도합니다...")
            try:
                # Attempt to reconnect
                self.is_connected = self.initialize_connection(st.session_state.session_id)
                if not self.is_connected:
                    st.warning("⚠️ WebSocket 재연결 실패. HTTP 모드로 전환됩니다.")
                    return None
            except Exception as e:
                st.warning(f"⚠️ WebSocket 재연결 오류: {str(e)}. HTTP 모드로 전환됩니다.")
                return None
        
        # Create message container for streaming
        message_container = st.empty()
        context_container = st.empty()
        status_container = st.empty()
        
        full_response = ""
        context_sources = []
        
        # Initialize variables for inner function
        current_model_type = model_type
        
        try:
            # Get configuration from session state
            rag_mode = st.session_state.get("rag_mode", "LangChain RAG")
            collection_names = st.session_state.get("selected_collections", None)
            
            # Show initial status
            with status_container.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%); 
                            color: white; padding: 1rem; border-radius: 10px; 
                            text-align: center; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                        <div style="animation: pulse 1.5s ease-in-out infinite; font-size: 1.2rem;">🤖</div>
                        <span style="font-size: 1.1rem; font-weight: 500;">AI가 응답을 생성하고 있습니다...</span>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.8;">
                        실시간 스트리밍 중
                    </div>
                </div>
                <style>
                @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.1); opacity: 0.7; }
                }
                </style>
                """, unsafe_allow_html=True)
            
            # Send message and get streaming response using asyncio
            import asyncio
            
            async def process_websocket_stream():
                nonlocal full_response, context_sources
                # Use local variable to avoid scope issues
                local_model_type = current_model_type
                
                async for data in self.ws_service.send_message_stream(
                    message, rag_mode, local_model_type, collection_names
                ):
                    if data["type"] == "error":
                        status_container.empty()
                        st.error(f"❌ {data['message']}")
                        return None
                    
                    elif data["type"] == "status":
                        # Update status message
                        with status_container.container():
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%); 
                                        color: white; padding: 1rem; border-radius: 10px; 
                                        text-align: center; margin: 1rem 0;">
                                <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                                    <div style="animation: pulse 1.5s ease-in-out infinite;">🤖</div>
                                    <span>{data['message']}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    elif data["type"] == "context":
                        context_sources = data.get("sources", [])
                        similarity_scores = data.get("similarity_scores", [])
                        context_count = data.get("context_count", 0)
                        source_collections = data.get("source_collections", [])
                        collections_used = data.get("collections_used", [])
                        multi_collection = data.get("multi_collection", False)
                        
                        if context_sources:
                            with context_container.container():
                                st.markdown("### 📚 참고 문서")
                                
                                # Show collection information
                                if multi_collection and collections_used:
                                    st.info(f"🔍 검색된 컬렉션: {', '.join(collections_used)}")
                                elif source_collections:
                                    st.info(f"🔍 검색된 컬렉션: {', '.join(source_collections)}")
                                
                                # Create detailed context display
                                for i, (source, similarity) in enumerate(zip(context_sources, similarity_scores), 1):
                                    similarity_percent = similarity * 100 if similarity else 0
                                    st.markdown(f"""
                                    <div style="background: #e3f2fd; padding: 0.5rem; border-radius: 5px; 
                                                margin: 0.25rem 0; border-left: 3px solid #2196F3;">
                                        <strong>{i}. {source}</strong> 
                                        <span style="color: #666; font-size: 0.9em;">(유사도: {similarity_percent:.1f}%)</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                if context_count > 0:
                                    if multi_collection:
                                        st.caption(f"총 {context_count}개의 관련 문서를 {len(collections_used)}개 컬렉션에서 참조했습니다.")
                                    else:
                                        st.caption(f"총 {context_count}개의 관련 문서를 참조했습니다.")
                        
                        # Clear status when context is received
                        status_container.empty()
                    
                    elif data["type"] == "chunk":
                        if not data.get("finished", False):
                            full_response += data["content"]
                            
                            # Real-time text update
                            with message_container.container():
                                st.markdown(f"""
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                                            border-left: 4px solid #007bff; margin: 0.5rem 0; 
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    <div style="font-weight: 500; color: #495057; margin-bottom: 0.5rem;">
                                        🤖 AI <span style="font-size: 0.8em; color: #6c757d;">({rag_mode})</span>
                                    </div>
                                    <div style="line-height: 1.6; color: #212529; white-space: pre-wrap;">{full_response}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            # Completion signal received
                            status_container.empty()
                            
                            # Show model information if available
                            model_info = data.get("model_info", {})
                            if model_info:
                                model_name = model_info.get("model_name", "Unknown")
                                response_model_type = model_info.get("model_type", local_model_type)
                                st.caption(f"🧠 모델: {model_name} ({response_model_type})")
                            
                            # Show RAG mode indicator
                            if rag_mode == "LangChain RAG":
                                st.caption("🧠 LangChain RAG 모드")
                            else:
                                st.caption("⚡ 기본 RAG 모드")
                            
                            return full_response
                
                return full_response
            
            # Run the async function
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(process_websocket_stream())
            return result
            
        except Exception as e:
            status_container.empty()
            st.error(f"메시지 전송 중 오류가 발생했습니다: {str(e)}")
            return None
    
    async def disconnect(self):
        """Disconnect WebSocket"""
        if self.ws_service:
            await self.ws_service.disconnect()
            self.is_connected = False
            st.info("웹소켓 연결이 종료되었습니다.")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        if self.ws_service:
            return self.ws_service.get_connection_status()
        return {"connected": False, "session_id": None, "websocket_url": None}
    
    async def health_check(self) -> bool:
        """Check WebSocket connection health"""
        if self.ws_service:
            return await self.ws_service.health_check()
        return False
