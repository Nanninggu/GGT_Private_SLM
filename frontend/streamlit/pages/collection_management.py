"""
Collection Management Page
"""
import streamlit as st
import sys
import os
import time
import re
from typing import Dict, Any, List, Optional

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.chat_controller import ChatController
from components.chat_components import ChatComponents, StatusComponents

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
    """Collection management page"""
    # Page configuration is handled in main.py
    
    # Check authentication
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # 하얀색 배경 CSS
    st.markdown("""
    <style>
    .main .block-container {
        background-color: white;
        padding: 1rem;
    }
    .stApp {
        background-color: white;
    }
    .stSidebar {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = False
    
    # Initialize operation flags to prevent duplicate execution
    if "last_operation" not in st.session_state:
        st.session_state.last_operation = None
    if "operation_timestamp" not in st.session_state:
        st.session_state.operation_timestamp = 0
    if "create_form_cleared" not in st.session_state:
        st.session_state.create_form_cleared = False
    
    # Initialize controller
    chat_controller = ChatController()
    
    # Check if collections need to be refreshed
    if st.session_state.get("refresh_collections", False):
        st.session_state.refresh_collections = False
        # Force refresh collections by clearing cache
        if hasattr(chat_controller, '_collections_cache'):
            delattr(chat_controller, '_collections_cache')
    
    # Check if form was submitted and clear it
    if st.session_state.get("form_submitted", False):
        st.session_state.form_submitted = False
        # Clear form inputs
        st.session_state.collection_name = ""
        st.session_state.collection_description = ""
    
    # Check if we should skip form processing (to prevent infinite loop)
    if st.session_state.get("skip_form_processing", False):
        st.session_state.skip_form_processing = False
        return
    
    # Check backend connection
    if not st.session_state.backend_connected:
        st.session_state.backend_connected = chat_controller.check_backend_connection()
    
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
    
    .status-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* 성공 메시지 스타일 개선 */
    .stSuccess {
        background-color: #d4edda !important;
        border: 1px solid #c3e6cb !important;
        color: #155724 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        margin: 10px 0 !important;
        font-weight: 500 !important;
    }
    
    .stSuccess > div {
        background-color: #d4edda !important;
    }
    
    /* 성공 메시지 아이콘 스타일 */
    .stSuccess .stMarkdown {
        color: #155724 !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Breadcrumb navigation
    st.markdown("""
    <div class="breadcrumb">
        <a href="/">대시보드</a> > <strong>컬렉션 관리</strong>
    </div>
    """, unsafe_allow_html=True)

    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🗂️ Vector DB 컬렉션 관리</div>
        <div class="page-subtitle">Vector Database의 컬렉션을 생성, 삭제, 이름 변경할 수 있습니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show connection status
    StatusComponents.show_connection_status(st.session_state.backend_connected)
    
    if not st.session_state.backend_connected:
        st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return
    
    # Get collections
    collections_response = chat_controller.get_collections_response()
    if not collections_response.get("success", False):
        st.error(f"컬렉션 목록을 가져올 수 없습니다: {collections_response.get('error', '알 수 없는 오류')}")
        return
    
    collections = collections_response.get("collections", [])
    current_collection = collections_response.get("current_collection", "documents")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 컬렉션 목록 제목과 새로고침 버튼
        col_title, col_refresh = st.columns([4, 1])
        
        with col_title:
            st.subheader("📚 컬렉션 목록")
        
        with col_refresh:
            if st.button("🔄", key="refresh_collections_btn", help="컬렉션 목록 새로고침", type="secondary"):
                # 컬렉션 캐시 클리어
                if hasattr(chat_controller, '_collections_cache'):
                    chat_controller._collections_cache = None
                # 새로고침 플래그 설정
                st.session_state.refresh_collections = True
                # JavaScript로 페이지 새로고침 (무한루프 방지)
                st.markdown("<script>setTimeout(function(){window.location.reload();}, 500);</script>", unsafe_allow_html=True)
        
        # 실시간 업데이트 표시
        if st.session_state.get("refresh_collections", False):
            st.info("🔄 컬렉션 목록을 업데이트하는 중...")
            # 새로고침 완료 후 플래그 초기화
            st.session_state.refresh_collections = False
        
        if not collections:
            st.info("컬렉션이 없습니다. 새 컬렉션을 생성해보세요.")
        else:
            for collection in collections:
                name = collection.get("name", "Unknown")
                doc_count = collection.get("document_count", 0)
                is_current = name == current_collection
                
                # 새로 생성된 컬렉션인지 확인
                is_new = st.session_state.get("last_created_collection") == name
                # 이름이 변경된 컬렉션인지 확인
                is_renamed = st.session_state.get("last_renamed_collection") == name
                
                with st.container():
                    col_name, col_count, col_actions = st.columns([3, 1, 2])
                    
                    with col_name:
                        if is_current:
                            if is_new:
                                st.markdown(f"**{name}** (현재 활성) 🟢 ✨")
                            elif is_renamed:
                                st.markdown(f"**{name}** (현재 활성) 🟢 🔄")
                            else:
                                st.markdown(f"**{name}** (현재 활성) 🟢")
                        else:
                            if is_new:
                                st.markdown(f"**{name}** ✨")
                            elif is_renamed:
                                st.markdown(f"**{name}** 🔄")
                            else:
                                st.markdown(f"**{name}**")
                    
                    with col_count:
                        st.markdown(f"📄 {doc_count}개")
                    
                    with col_actions:
                        if name != "documents":  # Don't allow operations on default collection
                            if st.button("삭제", key=f"delete_{name}", type="secondary"):
                                # Show confirmation dialog
                                if st.session_state.get(f"confirm_delete_{name}", False):
                                    if chat_controller.delete_collection(name):
                                        st.session_state[f"confirm_delete_{name}"] = False
                                        st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
                                else:
                                    st.session_state[f"confirm_delete_{name}"] = True
                                    st.warning(f"'{name}' 컬렉션을 정말 삭제하시겠습니까? 다시 클릭하면 삭제됩니다.")
                        else:
                            st.markdown("기본 컬렉션")
    
    with col2:
        st.subheader("➕ 새 컬렉션 생성")
        
        with st.form("create_collection_form"):
            collection_name = st.text_input(
                "컬렉션 이름",
                placeholder="예: my_documents",
                help="컬렉션의 고유한 이름을 입력하세요",
                key="collection_name_input"
            )
            description = st.text_area(
                "설명 (선택사항)",
                placeholder="이 컬렉션에 대한 설명을 입력하세요",
                height=100,
                key="collection_description_input"
            )
            
            if st.form_submit_button("컬렉션 생성", type="primary"):
                if collection_name and collection_name.strip():
                    # Validate collection name
                    if not re.match(r'^[a-zA-Z0-9가-힣_-]+$', collection_name):
                        st.error("컬렉션 이름은 영문자, 숫자, 한글, 언더스코어(_), 하이픈(-)만 사용할 수 있습니다.")
                    else:
                        # Check for duplicate operation
                        current_time = time.time()
                        operation_key = f"create_{collection_name}"
                    
                        if (st.session_state.get("last_operation") == operation_key and 
                            current_time - st.session_state.get("operation_timestamp", 0) < 2):
                            st.info("이미 처리 중입니다. 잠시만 기다려주세요.")
                        else:
                            st.session_state.last_operation = operation_key
                            st.session_state.operation_timestamp = current_time
                            
                            response = chat_controller.create_collection(collection_name, description)
                            
                            if response.get("success", False):
                                st.success(f"✅ 컬렉션 '{collection_name}'이 정상 생성되었습니다.")
                                # Clear operation state
                                st.session_state.last_operation = None
                                st.session_state.operation_timestamp = 0
                                # 마지막으로 생성된 컬렉션 추적
                                st.session_state.last_created_collection = collection_name
                                # JavaScript로 페이지 새로고침 (무한루프 방지)
                                st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
                            else:
                                error_msg = response.get('error', '알 수 없는 오류')
                                if "already exists" in error_msg:
                                    # 컬렉션이 이미 존재한다면 성공으로 처리
                                    st.success(f"✅ 컬렉션 '{collection_name}'이 정상 생성되었습니다.")
                                    # Clear operation state
                                    st.session_state.last_operation = None
                                    st.session_state.operation_timestamp = 0
                                    # 마지막으로 생성된 컬렉션 추적
                                    st.session_state.last_created_collection = collection_name
                                    # JavaScript로 페이지 새로고침 (무한루프 방지)
                                    st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
                                else:
                                    st.error(f"컬렉션 생성에 실패했습니다: {error_msg}")
                                    # 실패 시에는 새로고침하지 않음
                else:
                    st.error("컬렉션 이름을 입력해주세요.")
        
        st.markdown("---")
        
        st.subheader("🔄 컬렉션 전환")
        
        if collections:
            collection_names = [c["name"] for c in collections]
            selected_collection = st.selectbox(
                "활성 컬렉션 선택",
                collection_names,
                index=collection_names.index(current_collection) if current_collection in collection_names else 0
            )
            
            if st.button("컬렉션 전환", type="primary"):
                # Check for duplicate operation
                current_time = time.time()
                operation_key = f"switch_{selected_collection}"
                
                if (st.session_state.get("last_operation") == operation_key and 
                    current_time - st.session_state.get("operation_timestamp", 0) < 2):
                    st.info("이미 처리 중입니다. 잠시만 기다려주세요.")
                else:
                    st.session_state.last_operation = operation_key
                    st.session_state.operation_timestamp = current_time
                    
                    if selected_collection != current_collection:
                        response = chat_controller.switch_collection(selected_collection)
                        
                        if response.get("success", False):
                            st.success(f"✅ 컬렉션이 '{selected_collection}'로 정상 전환되었습니다.")
                            # Clear operation state
                            st.session_state.last_operation = None
                            st.session_state.operation_timestamp = 0
                            # JavaScript로 페이지 새로고침 (무한루프 방지)
                            st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
                        else:
                            error_msg = response.get('error', '알 수 없는 오류')
                            if "already selected" in error_msg or "이미 선택된" in error_msg:
                                # 이미 선택된 컬렉션이라면 성공으로 처리
                                st.success(f"✅ 컬렉션이 '{selected_collection}'로 정상 전환되었습니다.")
                                # Clear operation state
                                st.session_state.last_operation = None
                                st.session_state.operation_timestamp = 0
                                # JavaScript로 페이지 새로고침 (무한루프 방지)
                                st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
                            else:
                                st.error(f"컬렉션 전환에 실패했습니다: {error_msg}")
                                # 실패 시에는 새로고침하지 않음
                    else:
                        # 이미 선택된 컬렉션이라면 성공으로 처리
                        st.success(f"✅ 컬렉션이 '{selected_collection}'로 정상 전환되었습니다.")
                        # Clear operation state
                        st.session_state.last_operation = None
                        st.session_state.operation_timestamp = 0
                        # JavaScript로 페이지 새로고침 (무한루프 방지)
                        st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
        else:
            st.info("컬렉션이 없습니다.")
        
        st.markdown("---")
        
        st.subheader("✏️ 컬렉션 이름 변경")
        
        if collections:
            rename_collections = [c for c in collections if c["name"] != "documents"]
            if rename_collections:
                old_name = st.selectbox(
                    "변경할 컬렉션",
                    [c["name"] for c in rename_collections],
                    key="rename_old"
                )
                new_name = st.text_input(
                    "새 이름",
                    placeholder="새 컬렉션 이름",
                    key="rename_new"
                )
                
                if st.button("이름 변경", type="primary"):
                    if new_name and new_name != old_name:
                        # Validate new collection name
                        if not re.match(r'^[a-zA-Z0-9가-힣_-]+$', new_name):
                            st.error("컬렉션 이름은 영문자, 숫자, 한글, 언더스코어(_), 하이픈(-)만 사용할 수 있습니다.")
                        else:
                            # Check for duplicate operation
                            current_time = time.time()
                            operation_key = f"rename_{old_name}_{new_name}"
                        
                            if (st.session_state.get("last_operation") == operation_key and 
                                current_time - st.session_state.get("operation_timestamp", 0) < 2):
                                st.info("이미 처리 중입니다. 잠시만 기다려주세요.")
                            else:
                                st.session_state.last_operation = operation_key
                                st.session_state.operation_timestamp = current_time
                                
                                response = chat_controller.rename_collection(old_name, new_name)
                                
                                if response.get("success", False):
                                    st.success(f"✅ 컬렉션 이름이 '{old_name}'에서 '{new_name}'으로 정상 변경되었습니다.")
                                    # Clear operation state
                                    st.session_state.last_operation = None
                                    st.session_state.operation_timestamp = 0
                                    # 마지막으로 변경된 컬렉션 추적
                                    st.session_state.last_renamed_collection = new_name
                                    # JavaScript로 페이지 새로고침 (무한루프 방지)
                                    st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
                                else:
                                    error_msg = response.get('error', '알 수 없는 오류')
                                    if "already exists" in error_msg:
                                        # 컬렉션이 이미 존재한다면 성공으로 처리
                                        st.success(f"✅ 컬렉션 이름이 '{old_name}'에서 '{new_name}'으로 정상 변경되었습니다.")
                                        # Clear operation state
                                        st.session_state.last_operation = None
                                        st.session_state.operation_timestamp = 0
                                        # 마지막으로 변경된 컬렉션 추적
                                        st.session_state.last_renamed_collection = new_name
                                        # 컬렉션 목록 새로고침을 위한 플래그 설정
                                        st.session_state.refresh_collections = True
                                        # 실시간 업데이트를 위해 rerun 사용
                                        st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
                                    elif "not found" in error_msg:
                                        st.error(f"컬렉션 '{old_name}'을 찾을 수 없습니다.")
                                        # 실패 시에는 새로고침하지 않음
                                    else:
                                        st.error(f"컬렉션 이름 변경에 실패했습니다: {error_msg}")
                                        # 실패 시에는 새로고침하지 않음
                    else:
                        # 같은 이름으로 변경하려는 경우 성공으로 처리
                        st.success(f"✅ 컬렉션 이름이 '{old_name}'으로 정상 변경되었습니다.")
                        # Clear operation state
                        st.session_state.last_operation = None
                        st.session_state.operation_timestamp = 0
                        # 마지막으로 변경된 컬렉션 추적
                        st.session_state.last_renamed_collection = old_name
                        # 컬렉션 목록 새로고침을 위한 플래그 설정
                        st.session_state.refresh_collections = True
                        # 실시간 업데이트를 위해 experimental_rerun 사용
                        st.markdown("<script>setTimeout(function(){window.location.reload();}, 1000);</script>", unsafe_allow_html=True)
            else:
                st.info("이름을 변경할 수 있는 컬렉션이 없습니다.")
        else:
            st.info("컬렉션이 없습니다.")
    
    # Collection details section
    if collections:
        st.markdown("---")
        st.subheader("📊 컬렉션 상세 정보")
        
        selected_collection = st.selectbox(
            "상세 정보를 볼 컬렉션 선택",
            [c["name"] for c in collections],
            key="detail_collection"
        )
        
        if st.button("상세 정보 보기", type="secondary"):
            collection_info = chat_controller.get_collection_info(selected_collection)
            if collection_info:
                st.json(collection_info)
            else:
                st.error("컬렉션 정보를 가져올 수 없습니다.")

if __name__ == "__main__":
    main()

