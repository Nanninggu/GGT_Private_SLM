"""
File Upload Page for Streamlit
"""
import streamlit as st
import sys
import os

# Add parent directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from services.api_service import APIService
from components.chat_components import FileUploadComponents, StatusComponents

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
    """Main file upload page"""
    # Page configuration is handled in main.py
    
    # Check authentication
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # HAI Portal styling
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
    
    .breadcrumb {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    .breadcrumb a {
        color: #8B5CF6;
        text-decoration: none;
    }
    
    .breadcrumb a:hover {
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

    # Breadcrumb navigation
    st.markdown("""
    <div class="breadcrumb">
        <a href="/">대시보드</a> > <strong>파일 업로드</strong>
    </div>
    """, unsafe_allow_html=True)

    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">📁 파일 업로드</div>
        <div class="page-subtitle">문서를 업로드하여 RAG 시스템에 추가하고 벡터화합니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🏠 홈으로", use_container_width=True):
            st.switch_page("main.py")
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    # Initialize API service
    api_service = APIService()
    
    # Check backend connection
    if not api_service.health_check():
        StatusComponents.show_connection_status(False)
        st.stop()
    
    StatusComponents.show_connection_status(True)
    
    # RAG mode selector
    st.sidebar.title("⚙️ 설정")
    rag_mode = FileUploadComponents.render_rag_mode_selector()
    
    # Initialize selected_collection for all RAG modes
    selected_collection = "documents"  # Will be overridden based on RAG mode
    
    # Collection Selection
    if rag_mode == "LangChain RAG":
        st.sidebar.markdown("---")
        st.sidebar.subheader("📚 Vector DB 컬렉션")
        
        # Import here to avoid circular imports
        from controllers.chat_controller import ChatController
        chat_controller = ChatController()
        
        # Get collections
        collections = chat_controller.get_collections()
        current_collection = chat_controller.get_current_collection()
        
        # If no collections returned, create default collection
        if not collections:
            collections = [{
                "id": "default",
                "name": "langchain_documents",
                "metadata": {},
                "created_at": None,
                "document_count": 0
            }]
        
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
            selected_index = st.sidebar.selectbox(
                "업로드할 컬렉션 선택",
                range(len(collection_options)),
                format_func=lambda x: collection_options[x],
                index=current_collection_index,
                key="upload_collection_select"
            )
            
            if selected_index is not None:
                selected_collection = collections[selected_index]['name']
                st.sidebar.info(f"선택된 컬렉션: **{selected_collection}**")
                
                # Show collection info
                if st.sidebar.button("ℹ️ 컬렉션 정보", key="show_upload_collection_info"):
                    collection_info = chat_controller.get_collection_info(selected_collection)
                    if collection_info:
                        st.sidebar.json(collection_info)
        else:
            # Show default collection when no collections are available
            st.sidebar.info("기본 컬렉션을 사용합니다.")
            selected_collection = "langchain_documents"
            
            # Show current collection info
            if current_collection:
                st.sidebar.info(f"현재 활성 컬렉션: **{current_collection}**")
                selected_collection = current_collection
            
            # Refresh button
            if st.sidebar.button("🔄 새로고침", key="refresh_upload_collections"):
                st.rerun()
            
            # Show message about creating collections
            st.sidebar.markdown("""
            **컬렉션 생성 방법:**
            1. 파일을 업로드하면 자동으로 컬렉션이 생성됩니다
            2. LangChain RAG 모드로 업로드하세요
            """)
    else:
        # Basic RAG mode - show simple collection info
        st.sidebar.markdown("---")
        st.sidebar.subheader("📚 Vector DB 컬렉션")
        st.sidebar.info("기본 RAG 모드에서는 'documents' 컬렉션을 사용합니다.")
        st.sidebar.markdown("""
        **기본 RAG 모드:**
        - 기본 컬렉션 'documents'를 사용합니다
        - LangChain RAG 모드에서 컬렉션 관리가 가능합니다
        """)
    
    # Upload mode selector
    upload_mode = st.sidebar.radio(
        "업로드 모드",
        ["단일 파일", "여러 파일"],
        help="단일 파일: 하나씩 업로드\n여러 파일: 여러 개를 한 번에 업로드"
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if upload_mode == "단일 파일":
            # Single file uploader
            uploaded_file = FileUploadComponents.render_file_uploader(rag_mode, multiple=False)
            
            if uploaded_file is not None:
                # Upload button
                if FileUploadComponents.render_upload_button():
                    # Process file upload
                    with StatusComponents.show_loading():
                        try:
                            # Read file content
                            st.info("📁 파일을 읽는 중...")
                            file_content = uploaded_file.getvalue()
                            filename = uploaded_file.name
                            content_type = uploaded_file.type
                            st.info(f"✅ 파일 읽기 완료: {filename} ({len(file_content)} bytes)")
                            
                            # Upload to appropriate RAG system
                            st.info("🚀 서버로 파일을 전송하는 중...")
                            if rag_mode == "기본 RAG":
                                result = api_service.upload_file(file_content, filename, content_type, selected_collection)
                            else:  # LangChain RAG
                                result = api_service.upload_file_langchain(file_content, filename, content_type, selected_collection)
                            
                            if result.get("success", False):
                                # Show success message
                                if rag_mode == "기본 RAG":
                                    FileUploadComponents.show_upload_success(
                                        filename, 
                                        doc_id=result.get("document_id")
                                    )
                                else:
                                    FileUploadComponents.show_upload_success(
                                        filename, 
                                        doc_ids=result.get("document_ids")
                                    )
                                
                                # Show additional info
                                st.info(f"📊 파일 크기: {result.get('size', 0)} bytes")
                                st.info(f"📝 추출된 텍스트 길이: {result.get('extracted_text_length', 0)} 문자")
                                st.info(f"🔧 추출 방법: {result.get('extraction_method', 'unknown')}")
                                st.info(f"🎯 RAG 모드: {rag_mode}")
                                
                            else:
                                error_msg = result.get("error", "알 수 없는 오류")
                                if "timeout" in error_msg.lower():
                                    error_msg += "\n\n💡 해결 방법:\n- 파일 크기를 줄여보세요\n- 네트워크 연결을 확인하세요\n- 잠시 후 다시 시도해보세요"
                                FileUploadComponents.show_upload_error(error_msg)
                                
                        except Exception as e:
                            error_msg = str(e)
                            if "timeout" in error_msg.lower():
                                error_msg += "\n\n💡 해결 방법:\n- 파일 크기를 줄여보세요\n- 네트워크 연결을 확인하세요\n- 잠시 후 다시 시도해보세요"
                            FileUploadComponents.show_upload_error(error_msg)
        
        else:  # Multiple files
            # Multiple files uploader
            uploaded_files = FileUploadComponents.render_file_uploader(rag_mode, multiple=True)
            
            if uploaded_files:
                # Upload button
                if FileUploadComponents.render_upload_button():
                    # Process multiple files upload
                    with StatusComponents.show_loading():
                        try:
                            # Prepare file list
                            st.info(f"📁 {len(uploaded_files)}개 파일을 읽는 중...")
                            file_list = []
                            for i, uploaded_file in enumerate(uploaded_files):
                                st.info(f"  📄 파일 {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                                file_list.append({
                                    'filename': uploaded_file.name,
                                    'content': uploaded_file.getvalue(),
                                    'content_type': uploaded_file.type
                                })
                            st.info("✅ 모든 파일 읽기 완료")
                            
                            # Upload to appropriate RAG system
                            st.info("🚀 서버로 파일들을 전송하는 중...")
                            if rag_mode == "기본 RAG":
                                result = api_service.upload_multiple_files(file_list, selected_collection)
                            else:  # LangChain RAG
                                result = api_service.upload_multiple_files_langchain(file_list, selected_collection)
                            
                            if result.get("success", False):
                                # Show success message
                                st.success(f"✅ {result.get('message', '파일 업로드 완료')}")
                                
                                # Show detailed results
                                st.write("**업로드 결과:**")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("전체 파일", result.get('total_files', 0))
                                with col2:
                                    st.metric("성공", result.get('successful_uploads', 0))
                                with col3:
                                    st.metric("실패", result.get('failed_uploads', 0))
                                
                                # Show individual file results
                                st.write("**파일별 상세 결과:**")
                                for file_result in result.get('results', []):
                                    if file_result['success']:
                                        st.success(f"✅ {file_result['filename']} - 성공")
                                        if 'document_id' in file_result:
                                            st.caption(f"문서 ID: {file_result['document_id']}")
                                        if 'document_ids' in file_result:
                                            st.caption(f"문서 ID: {', '.join(file_result['document_ids'])}")
                                        st.caption(f"추출 방법: {file_result.get('extraction_method', 'unknown')}")
                                    else:
                                        st.error(f"❌ {file_result['filename']} - 실패: {file_result.get('error', '알 수 없는 오류')}")
                                
                            else:
                                error_msg = result.get("error", "알 수 없는 오류")
                                if "timeout" in error_msg.lower():
                                    error_msg += "\n\n💡 해결 방법:\n- 파일 크기를 줄여보세요\n- 네트워크 연결을 확인하세요\n- 잠시 후 다시 시도해보세요"
                                FileUploadComponents.show_upload_error(error_msg)
                                
                        except Exception as e:
                            error_msg = str(e)
                            if "timeout" in error_msg.lower():
                                error_msg += "\n\n💡 해결 방법:\n- 파일 크기를 줄여보세요\n- 네트워크 연결을 확인하세요\n- 잠시 후 다시 시도해보세요"
                            FileUploadComponents.show_upload_error(error_msg)
    
    with col2:
        # Information panel
        st.subheader("ℹ️ 업로드 정보")
        
        st.markdown("""
        **지원되는 파일 형식:**
        - 📄 텍스트 파일 (.txt, .md)
        - 📊 데이터 파일 (.csv, .json)
        - 📋 문서 파일 (.pdf, .docx)
        """)
        
        st.markdown("""
        **RAG 모드 설명:**
        - **기본 RAG**: 단순한 벡터 검색
        - **LangChain RAG**: 고급 체인 처리 및 메모리
        """)
        
        st.markdown("""
        **처리 과정:**
        1. 파일 업로드
        2. 텍스트 추출
        3. 벡터 임베딩 생성
        4. documents 테이블에 저장
        5. RAG 시스템에서 활용 가능
        """)
        
        st.markdown("""
        **⚠️ 주의사항:**
        - 대용량 파일은 처리 시간이 오래 걸릴 수 있습니다 (최대 10분)
        - CSV 파일의 경우 10MB 이상은 청크 단위로 처리됩니다
        - 타임아웃 발생 시 파일 크기를 줄이거나 잠시 후 다시 시도해보세요
        - 네트워크 연결이 안정적인지 확인하세요
        """)
        
        # Show current RAG mode and collection
        st.info(f"현재 선택된 모드: **{rag_mode}**")
        st.info(f"현재 선택된 컬렉션: **{selected_collection}**")

if __name__ == "__main__":
    main()
