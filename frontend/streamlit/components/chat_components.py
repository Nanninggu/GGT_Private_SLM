"""
Chat components for Streamlit UI
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import io

class ChatComponents:
    """Reusable chat UI components"""

    @staticmethod
    def render_message(message: Dict[str, Any]):
        """Render a single chat message with HAI Portal styling"""
        role = message["role"]
        content = message["content"]
        timestamp = message.get("timestamp", "")
        context = message.get("context", [])
        metadata = message.get("metadata", {})

        if role == "user":
            with st.chat_message("user"):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%); 
                            color: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                if timestamp:
                    st.caption(f"👤 사용자 • {ChatComponents._format_timestamp(timestamp)}")
        else:
            with st.chat_message("assistant"):
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                            border-left: 4px solid #8B5CF6; margin: 0.5rem 0;">
                    {content}
                </div>
                """, unsafe_allow_html=True)
                
                # Display source information if available
                if context and len(context) > 0:
                    st.markdown("---")
                    st.markdown("📚 **참조 출처:**")
                    
                    for i, source in enumerate(context, 1):
                        filename = source.get("filename", "Unknown")
                        page = source.get("page_number", 1)
                        collection = source.get("collection", "documents")
                        similarity = source.get("similarity", 0)
                        
                        with st.expander(f"{i}. {filename} (페이지 {page}, 컬렉션: {collection})", expanded=False):
                            st.write(f"**파일명:** {filename}")
                            st.write(f"**페이지:** {page}")
                            st.write(f"**컬렉션:** {collection}")
                            st.write(f"**유사도:** {similarity:.2f}")
                            if source.get("source_url"):
                                st.write(f"**URL:** {source['source_url']}")
                            if source.get("upload_date"):
                                st.write(f"**업로드 날짜:** {source['upload_date']}")
                            
                            # Show content preview
                            content_preview = source.get("content", "")[:200]
                            if len(source.get("content", "")) > 200:
                                content_preview += "..."
                            st.write(f"**내용 미리보기:** {content_preview}")
                
                if timestamp:
                    st.caption(f"🤖 {ChatComponents._format_timestamp(timestamp)}")

    @staticmethod
    def render_chat_history(messages: List[Dict[str, Any]]):
        """Render the entire chat history"""
        if not messages:
            st.info("채팅을 시작해보세요! 👋")
            return

        for message in messages:
            ChatComponents.render_message(message)

    @staticmethod
    def render_sidebar():
        """Render sidebar with HAI Portal navigation"""
        with st.sidebar:
            # HAI Portal branding
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #8B5CF6;">
                <h1 style="color: #8B5CF6; margin: 0; font-size: 1.8rem;">HAI Portal</h1>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # HAI-Chat section (current)
            st.markdown("### 💬 HAI-Chat")
            st.markdown('<div style="background: #e3f2fd; padding: 0.5rem; border-radius: 5px; margin: 0.5rem 0;">현재 선택된 서비스</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Settings and logout
            st.markdown("### ⚙️ 설정")
            if st.button("🔧 설정", key="nav_settings", use_container_width=True):
                st.info("설정 페이지는 준비 중입니다.")
            
            if st.button("🚪 로그아웃", key="nav_logout", use_container_width=True):
                st.info("로그아웃 기능은 준비 중입니다.")
            
            st.markdown("---")
            
            # Chat controls
            st.markdown("### 💬 채팅 제어")
            if st.button("🗑️ 채팅 초기화", key="clear_chat", use_container_width=True):
                return "clear_chat"
            
            # Response Mode selection
            st.subheader("응답 모드")
            
            # Streaming option
            streaming_enabled = st.checkbox(
                "🚀 실시간 스트리밍",
                value=st.session_state.get("streaming_enabled", True),
                key="streaming_checkbox",
                help="ChatGPT처럼 실시간으로 텍스트가 타이핑되는 효과"
            )
            st.session_state.streaming_enabled = streaming_enabled
            
            if streaming_enabled:
                st.success("✨ 실시간 스트리밍 활성화")
            else:
                st.info("📝 일반 응답 모드")
            
            # RAG Mode selection
            st.subheader("RAG 모드")
            
            # Get current rag_mode and convert to index
            current_rag_mode = st.session_state.get("rag_mode", "기본 RAG")
            rag_options = ["기본 RAG", "LangChain RAG"]
            current_index = rag_options.index(current_rag_mode) if current_rag_mode in rag_options else 0
            
            rag_mode = st.selectbox(
                "RAG 시스템 선택",
                rag_options,
                index=current_index,
                key="rag_mode_select"
            )
            st.session_state.rag_mode = rag_mode
            
            if rag_mode == "LangChain RAG":
                st.info("🧠 LangChain 기반 RAG\n- 대화 메모리 지원\n- 고급 문서 검색\n- 체인 기반 처리")
            else:
                st.info("⚡ 기본 RAG\n- 빠른 응답\n- 간단한 검색")
            
            # Collection Selection (only for LangChain RAG)
            if rag_mode == "LangChain RAG":
                st.markdown("---")
                st.subheader("📚 Vector DB 컬렉션")
                
                # Import here to avoid circular imports
                from controllers.chat_controller import ChatController
                chat_controller = ChatController()
                
                # Get collections
                collections = chat_controller.get_collections()
                current_collection = chat_controller.get_current_collection()
                
                # Debug: Show collections info
                st.write(f"🔍 Debug - Collections: {collections}")
                st.write(f"🔍 Debug - Current Collection: {current_collection}")
                
                # If no collections returned, create default collection
                if not collections:
                    collections = [{
                        "id": "default",
                        "name": "documents",
                        "metadata": {},
                        "created_at": None,
                        "document_count": 0
                    }]
                
                # Always show collection selection UI
                if collections:
                    # Create collection options
                    collection_options = [f"{col['name']} ({col.get('document_count', 0)}개 문서)" for col in collections]
                    
                    # Find current collection index
                    current_collection_index = 0
                    for i, col in enumerate(collections):
                        if col['name'] == current_collection:
                            current_collection_index = i
                            break
                    
                    # Collection selector
                    selected_index = st.selectbox(
                        "사용할 컬렉션 선택",
                        range(len(collection_options)),
                        format_func=lambda x: collection_options[x],
                        index=current_collection_index,
                        key="collection_select"
                    )
                    
                    if selected_index is not None:
                        selected_collection = collections[selected_index]['name']
                        
                        # Show collection info
                        if st.button("ℹ️ 컬렉션 정보 보기", key="show_collection_info"):
                            collection_info = chat_controller.get_collection_info(selected_collection)
                            if collection_info:
                                st.json(collection_info)
                        
                        # Switch collection if different
                        if selected_collection != current_collection:
                            if st.button("🔄 컬렉션 전환", key="switch_collection"):
                                if chat_controller.switch_collection(selected_collection):
                                    st.rerun()
                    
                    # Show current collection info
                    if current_collection:
                        st.info(f"현재 활성 컬렉션: **{current_collection}**")
                else:
                    # Show default collection when no collections are available
                    st.info("기본 컬렉션을 사용합니다.")
                    
                    # Show current collection info
                    if current_collection:
                        st.info(f"현재 활성 컬렉션: **{current_collection}**")
                    
                    # Refresh button
                    if st.button("🔄 컬렉션 목록 새로고침", key="refresh_collections"):
                        st.rerun()
                    
                    # Collection management button
                    if st.button("🗂️ 컬렉션 관리", key="collection_management", use_container_width=True):
                        st.switch_page("pages/collection_management.py")
                    
                    # Show message about creating collections
                    st.markdown("""
                    **컬렉션 생성 방법:**
                    1. 컬렉션 관리 페이지에서 직접 생성
                    2. 파일 업로드 페이지에서 문서를 업로드
                    3. LangChain RAG 모드로 업로드
                    """)

            # Session management
            st.subheader("세션 관리")
            st.text_input("현재 세션 ID", value=st.session_state.get("session_id", ""), disabled=True)

            # Connection status
            st.subheader("연결 상태")
            if st.session_state.get("backend_connected", False):
                st.success("✅ 백엔드 연결됨")
            else:
                st.error("❌ 백엔드 연결 실패")

            if st.button("🔄 연결 확인", key="check_connection"):
                return "check_connection"

        return None

    @staticmethod
    def render_chat_input():
        """Render chat input component"""
        return st.chat_input("메시지를 입력하세요...")

    @staticmethod
    def _format_timestamp(timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return timestamp_str

class StatusComponents:
    """Components for displaying status information"""

    @staticmethod
    def show_connection_status(connected: bool):
        """Show connection status"""
        if connected:
            st.success("🟢 백엔드 서버에 연결되었습니다.")
        else:
            st.error("🔴 백엔드 서버에 연결할 수 없습니다. 서버를 시작해주세요.")

    @staticmethod
    def show_loading():
        """Show loading indicator"""
        return st.spinner("처리 중...")

    @staticmethod
    def show_error(message: str):
        """Show error message"""
        st.error(f"❌ 오류: {message}")

class FileUploadComponents:
    """Components for file upload functionality"""

    @staticmethod
    def render_file_uploader(rag_mode: str = "기본 RAG", multiple: bool = False) -> Optional[st.runtime.uploaded_file_manager.UploadedFile]:
        """Render file uploader widget"""
        st.subheader("📁 파일 업로드")
        st.write("문서를 업로드하여 RAG 시스템에 추가할 수 있습니다.")
        
        # Supported file types
        supported_types = ["txt", "md", "pdf", "docx", "csv", "json"]
        
        if multiple:
            uploaded_files = st.file_uploader(
                "파일들을 선택하세요 (여러 개 선택 가능)",
                type=supported_types,
                accept_multiple_files=True,
                help=f"지원되는 파일 형식: {', '.join(supported_types)}",
                key=f"file_uploader_multiple_{rag_mode}"
            )
            
            if uploaded_files:
                st.write(f"**선택된 파일 수:** {len(uploaded_files)}개")
                
                # Display file info for each file
                for i, uploaded_file in enumerate(uploaded_files):
                    with st.expander(f"📄 {uploaded_file.name}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**파일명:** {uploaded_file.name}")
                        with col2:
                            st.write(f"**크기:** {len(uploaded_file.getvalue())} bytes")
                        with col3:
                            st.write(f"**타입:** {uploaded_file.type}")
                        
                        # Show file content preview for text files
                        if uploaded_file.type.startswith('text/'):
                            st.write("**파일 내용 미리보기:**")
                            content = uploaded_file.getvalue().decode('utf-8')
                            preview = content[:300] + "..." if len(content) > 300 else content
                            st.text_area("", preview, height=80, disabled=True, key=f"preview_{i}")
            
            return uploaded_files
        else:
            uploaded_file = st.file_uploader(
                "파일을 선택하세요",
                type=supported_types,
                help=f"지원되는 파일 형식: {', '.join(supported_types)}",
                key=f"file_uploader_{rag_mode}"
            )
            
            if uploaded_file is not None:
                # Display file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**파일명:** {uploaded_file.name}")
                with col2:
                    st.write(f"**크기:** {len(uploaded_file.getvalue())} bytes")
                with col3:
                    st.write(f"**타입:** {uploaded_file.type}")
                
                # Show file content preview for text files
                if uploaded_file.type.startswith('text/'):
                    st.write("**파일 내용 미리보기:**")
                    content = uploaded_file.getvalue().decode('utf-8')
                    preview = content[:500] + "..." if len(content) > 500 else content
                    st.text_area("", preview, height=100, disabled=True)
            
            return uploaded_file

    @staticmethod
    def render_upload_progress():
        """Render upload progress indicator"""
        return st.progress(0)

    @staticmethod
    def show_upload_success(filename: str, doc_id: str = None, doc_ids: List[str] = None):
        """Show upload success message"""
        if doc_id:
            st.success(f"✅ 파일 '{filename}'이 성공적으로 업로드되었습니다! (문서 ID: {doc_id})")
        elif doc_ids:
            st.success(f"✅ 파일 '{filename}'이 성공적으로 업로드되었습니다! (문서 ID: {', '.join(doc_ids)})")
        else:
            st.success(f"✅ 파일 '{filename}'이 성공적으로 업로드되었습니다!")

    @staticmethod
    def show_upload_error(error_message: str):
        """Show upload error message"""
        st.error(f"❌ 업로드 실패: {error_message}")

    @staticmethod
    def render_rag_mode_selector() -> str:
        """Render RAG mode selector for file upload"""
        st.write("**RAG 모드 선택:**")
        rag_mode = st.radio(
            "업로드할 RAG 시스템을 선택하세요:",
            ["기본 RAG", "LangChain RAG"],
            help="기본 RAG: 단순한 벡터 검색\nLangChain RAG: 고급 체인 처리 및 메모리"
        )
        return rag_mode

    @staticmethod
    def render_upload_button():
        """Render upload button"""
        return st.button("🚀 파일 업로드 및 벡터화", type="primary", use_container_width=True)

    @staticmethod
    def show_success(message: str):
        """Show success message"""
        st.success(f"✅ {message}")
