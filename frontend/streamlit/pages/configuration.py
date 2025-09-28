"""
Configuration Page - 시스템 설정 및 관리
"""
import streamlit as st

# 페이지 설정은 main.py에서 처리됨
import sys
import os
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.chat_controller import ChatController
from components.chat_components import StatusComponents


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
    """Configuration page"""
    # Page configuration is handled in main.py
    
    # Check authentication
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # Initialize session state
    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = False
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    
    # Initialize controller
    chat_controller = ChatController()
    
    # Check backend connection
    if not st.session_state.backend_connected:
        st.session_state.backend_connected = chat_controller.check_backend_connection()
    
    # Modern Enterprise UI - Pure White Configuration Theme
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
    
    /* Global styling - Pure White Background */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Adjust main content padding */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        background-color: #ffffff;
    }
    
    /* Modern Enterprise page header - Clean White Design */
    .page-header {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        margin-bottom: 3rem;
        color: #212529;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .page-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6c757d 0%, #495057 50%, #6c757d 100%);
    }
    
    .page-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.75rem;
        letter-spacing: -0.03em;
        color: #212529;
        text-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .page-subtitle {
        font-size: 1.3rem;
        opacity: 0.8;
        font-weight: 500;
        color: #6c757d;
    }
    
    .breadcrumb {
        color: #6c757d;
        font-size: 1rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    
    .breadcrumb a {
        color: #6c757d;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    
    .breadcrumb a:hover {
        color: #495057;
        text-decoration: underline;
    }
    
    /* Modern Enterprise config section - Pure White */
    .config-section {
        background: #ffffff;
        padding: 3rem;
        border-radius: 24px;
        margin-bottom: 2.5rem;
        position: relative;
        overflow: hidden;
    }
    
    .config-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
    }
    
    /* Modern Enterprise status card - Clean White Design */
    .status-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        border-left: 4px solid #6c757d;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        background: #f8f9fa;
    }
    
    .status-online {
        border-left-color: #10B981;
        background: #f0fdf4;
    }
    
    .status-offline {
        border-left-color: #EF4444;
        background: #fef2f2;
    }
    
    /* Modern Enterprise button styling */
    .stButton > button {
        border-radius: 16px;
        font-weight: 600;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid transparent;
        font-size: 1rem;
        padding: 0.75rem 1.5rem;
    }
    
    .stButton > button:hover {
        background: #f8f9fa;
    }
    
    /* Modern Enterprise input styling */
    .stTextInput > div > div > input {
        border-radius: 16px;
        padding: 1rem 1.25rem;
        font-size: 1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        background: #ffffff;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input:focus {
        background: #ffffff;
    }
    
    /* Modern Enterprise selectbox styling */
    .stSelectbox > div > div {
        border-radius: 16px;
        background: #ffffff;
    }
    
    /* Modern Enterprise radio button styling */
    .stRadio > div {
        gap: 1.5rem;
    }
    
    .stRadio > div > label {
        background: #ffffff;
        padding: 1.25rem;
        border-radius: 16px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        font-weight: 600;
    }
    
    .stRadio > div > label:hover {
        background: #f8f9fa;
    }
    
    /* Modern Enterprise checkbox styling */
    .stCheckbox > label {
        font-weight: 600;
        color: #212529;
        font-size: 1rem;
    }
    
    /* Modern Enterprise tabs styling */
    .stTabs > div > div > div > div {
        background: #ffffff;
        border-radius: 20px;
    }
    
    /* Tab selection styling - Red underline for selected tab */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #ffffff;
        border-bottom: 1px solid #e9ecef;
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        padding: 1rem 1.5rem;
        margin: 0;
        border-radius: 0;
        position: relative;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #f8f9fa;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: transparent;
        color: #dc3545;
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"]::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: #dc3545;
        border-radius: 2px 2px 0 0;
    }
    
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) {
        color: #6c757d;
    }
    
    .stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover {
        color: #495057;
    }
    
    /* Modern Enterprise expander styling */
    .streamlit-expander {
        border-radius: 16px;
        background: #ffffff;
    }
    
    /* Modern Enterprise metric styling */
    .metric-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: #f8f9fa;
    }
    
    /* Collection management cards */
    .collection-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .collection-card:hover {
        background: #f8f9fa;
    }
    
    /* Session management cards */
    .session-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .session-card:hover {
        background: #f8f9fa;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .page-header {
            padding: 3rem 1.5rem;
        }
        
        .page-title {
            font-size: 2.5rem;
        }
        
        .config-section {
            padding: 2rem 1.5rem;
            margin: 1rem;
        }
        
        .collection-card, .session-card {
            padding: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Navigation section removed - clean top layout

    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">⚙️ 시스템 설정</div>
        <div class="page-subtitle">Vector DB, 세션 및 연결 상태를 관리합니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show connection status
    StatusComponents.show_connection_status(st.session_state.backend_connected)
    
    if not st.session_state.backend_connected:
        st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3 = st.tabs(["🗂️ Vector DB 관리", "📋 세션 관리", "🔗 연결 상태"])
    
    with tab1:
        render_vector_db_management(chat_controller)
    
    with tab2:
        render_session_management(chat_controller)
        render_debug_settings()
    
    with tab3:
        render_connection_status(chat_controller)

def render_debug_settings():
    """Render debug settings section"""
    st.markdown("---")
    st.subheader("🔧 디버그 설정")
    
    # Debug mode toggle
    debug_mode = st.checkbox(
        "디버그 모드 활성화", 
        value=st.session_state.get("debug_mode", False),
        help="채팅 히스토리 로딩 과정을 디버깅할 수 있습니다."
    )
    
    if debug_mode != st.session_state.get("debug_mode", False):
        st.session_state.debug_mode = debug_mode
        if debug_mode:
            st.success("디버그 모드가 활성화되었습니다. 메인 페이지에서 디버그 정보를 확인할 수 있습니다.")
        else:
            st.info("디버그 모드가 비활성화되었습니다.")
    
    if debug_mode:
        st.info("💡 디버그 모드가 활성화되어 있습니다. 메인 페이지에서 채팅 히스토리 로딩 과정을 확인할 수 있습니다.")

def render_vector_db_management(chat_controller):
    """Render Vector DB management section"""
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    
    st.subheader("📚 Vector DB 컬렉션 관리")
    st.write("Vector Database의 컬렉션을 생성, 삭제, 이름 변경할 수 있습니다.")
    
    
    # Get collections (use cached data if available)
    if st.session_state.get("collections_data"):
        collections_response = st.session_state.collections_data
    else:
        with st.spinner("컬렉션 목록을 불러오는 중..."):
            collections_response = chat_controller.get_collections_response()
            st.session_state.collections_data = collections_response
    
    if not collections_response.get("success", False):
        st.error(f"컬렉션 목록을 가져올 수 없습니다: {collections_response.get('error', '알 수 없는 오류')}")
        return
    
    collections = collections_response.get("collections", [])
    current_collection = collections_response.get("current_collection", "documents")
    
    # 중복 제거를 위해 컬렉션을 딕셔너리로 변환 (name을 키로 사용)
    unique_collections = {}
    for collection in collections:
        name = collection.get("name", "Unknown")
        if name not in unique_collections:
            unique_collections[name] = collection
        else:
            # 중복된 경우 문서 수를 합산
            unique_collections[name]["document_count"] += collection.get("document_count", 0)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 컬렉션 목록 제목과 새로고침 버튼
        col_title, col_refresh = st.columns([4, 1])
        
        with col_title:
            st.markdown("#### 📚 내 컬렉션 목록")
            st.caption("💡 각 사용자는 자신만의 개인 컬렉션을 관리할 수 있습니다")
        
        with col_refresh:
            # 새로고침 버튼 클릭 처리
            if st.button("🔄", key="refresh_collections_btn", help="컬렉션 목록 새로고침", type="secondary"):
                # 컬렉션 캐시 클리어
                if hasattr(chat_controller, '_collections_cache'):
                    delattr(chat_controller, '_collections_cache')
                
                # 즉시 컬렉션 다시 가져오기
                try:
                    collections_response = chat_controller.get_collections_response()
                    if collections_response.get("success", False):
                        st.success("✅ 컬렉션 목록이 새로고침되었습니다.")
                        # 컬렉션 데이터 업데이트
                        st.session_state.collections_data = collections_response
                    else:
                        st.error("❌ 컬렉션 목록 새로고침에 실패했습니다.")
                except Exception as e:
                    st.error(f"❌ 새로고침 중 오류가 발생했습니다: {str(e)}")
        
        if not unique_collections:
            st.info("컬렉션이 없습니다. 새 컬렉션을 생성해보세요.")
        else:
            
            for idx, (name, collection) in enumerate(unique_collections.items()):
                doc_count = collection.get("document_count", 0)
                is_current = name == current_collection
                user_id = collection.get("user_id")
                is_shared = user_id is None
                
                with st.container():
                    col_name, col_count, col_actions = st.columns([3, 1, 2])
                    
                    with col_name:
                        if is_current:
                            if is_shared:
                                st.markdown(f"**{name}** (현재 활성) 🟢 🌐")
                                st.caption("공유 컬렉션")
                            else:
                                st.markdown(f"**{name}** (현재 활성) 🟢 👤")
                                st.caption("개인 컬렉션")
                        else:
                            if is_shared:
                                st.markdown(f"**{name}** 🌐")
                                st.caption("공유 컬렉션")
                            else:
                                st.markdown(f"**{name}** 👤")
                                st.caption("개인 컬렉션")
                    
                    with col_count:
                        st.markdown(f"📄 {doc_count}개")
                    
                    with col_actions:
                        if name != "documents" and name != "langchain_documents":  # Don't allow operations on default collections
                            # Check if user can delete this collection
                            can_delete = True
                            if is_shared:
                                # For shared collections, check if current user is the creator
                                created_by = collection.get("created_by")
                                current_user_id = st.session_state.get("user_info", {}).get("id")
                                can_delete = created_by == current_user_id
                            
                            if can_delete:
                                if st.button("삭제", key=f"delete_{name}_{idx}", type="secondary"):
                                    # Show confirmation dialog
                                    if st.session_state.get(f"confirm_delete_{name}", False):
                                        try:
                                            # Show loading indicator
                                            with st.spinner("컬렉션을 삭제하는 중..."):
                                                if chat_controller.delete_collection(name):
                                                    st.success(f"✅ 컬렉션 '{name}'이 삭제되었습니다.")
                                                    st.session_state[f"confirm_delete_{name}"] = False
                                                    
                                                    # 즉시 UI에서 해당 컬렉션 제거 (캐시 무효화)
                                                    if hasattr(chat_controller, '_collections_cache'):
                                                        delattr(chat_controller, '_collections_cache')
                                                    
                                                    # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                                                    if 'collections_data' in st.session_state:
                                                        del st.session_state.collections_data
                                                    
                                                    # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                                                    st.markdown("""
                                                    <script>
                                                    setTimeout(function() {
                                                        window.location.reload();
                                                    }, 1000);
                                                    </script>
                                                    """, unsafe_allow_html=True)
                                                else:
                                                    st.error(f"❌ 컬렉션 '{name}' 삭제에 실패했습니다.")
                                        except Exception as e:
                                            st.error(f"❌ 컬렉션 삭제 중 오류가 발생했습니다: {str(e)}")
                                else:
                                    st.session_state[f"confirm_delete_{name}"] = True
                                    st.warning(f"'{name}' 컬렉션을 정말 삭제하시겠습니까? 다시 클릭하면 삭제됩니다.")
                            else:
                                # 공유 컬렉션의 경우 삭제 권한이 없을 때 안내 메시지
                                st.caption("🔒 생성자만 삭제 가능")
                        else:
                            st.markdown("기본 컬렉션")
    
    with col2:
        st.markdown("#### ➕ 새 컬렉션 생성")
        
        with st.form("create_collection_form"):
            # 컬렉션 타입 선택
            collection_type = st.radio(
                "컬렉션 타입",
                ["개인 컬렉션", "공유 컬렉션"],
                help="개인 컬렉션: 나만 접근 가능\n공유 컬렉션: 모든 사용자가 접근 가능",
                key="collection_type_input"
            )
            
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
            
            # 컬렉션 타입에 따른 안내 메시지
            if collection_type == "개인 컬렉션":
                st.info("👤 **개인 컬렉션**: 나만 접근할 수 있는 개인 전용 컬렉션입니다.")
            else:
                st.warning("🌐 **공유 컬렉션**: 모든 사용자가 접근할 수 있는 공유 컬렉션입니다.")
            
            if st.form_submit_button("컬렉션 생성", type="primary"):
                if collection_name and collection_name.strip():
                    # Validate collection name
                    if not re.match(r'^[a-zA-Z0-9가-힣_-]+$', collection_name):
                        st.error("컬렉션 이름은 영문자, 숫자, 한글, 언더스코어(_), 하이픈(-)만 사용할 수 있습니다.")
                    else:
                        try:
                            # 컬렉션 타입에 따라 다른 API 호출
                            if collection_type == "개인 컬렉션":
                                response = chat_controller.create_collection(collection_name, description)
                                collection_type_icon = "👤"
                                collection_type_text = "개인"
                            else:  # 공유 컬렉션
                                response = chat_controller.create_shared_collection(collection_name, description)
                                collection_type_icon = "🌐"
                                collection_type_text = "공유"
                            
                            if response.get("success", False):
                                st.success(f"✅ {collection_type_text} 컬렉션 '{collection_name}'이 정상 생성되었습니다. {collection_type_icon}")
                                # 컬렉션 데이터 새로고침
                                if hasattr(chat_controller, '_collections_cache'):
                                    delattr(chat_controller, '_collections_cache')
                                # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                                if 'collections_data' in st.session_state:
                                    del st.session_state.collections_data
                                # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                                st.markdown("""
                                <script>
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                                </script>
                                """, unsafe_allow_html=True)
                            else:
                                error_msg = response.get('error', '알 수 없는 오류')
                                if "already exists" in error_msg:
                                    st.success(f"✅ {collection_type_text} 컬렉션 '{collection_name}'이 정상 생성되었습니다. {collection_type_icon}")
                                    # 컬렉션 데이터 새로고침
                                    if hasattr(chat_controller, '_collections_cache'):
                                        delattr(chat_controller, '_collections_cache')
                                    # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                                    if 'collections_data' in st.session_state:
                                        del st.session_state.collections_data
                                    # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                                    st.markdown("""
                                    <script>
                                    setTimeout(function() {
                                        window.location.reload();
                                    }, 1000);
                                    </script>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.error(f"{collection_type_text} 컬렉션 생성에 실패했습니다: {error_msg}")
                        except Exception as e:
                            st.error(f"❌ {collection_type_text} 컬렉션 생성 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.error("컬렉션 이름을 입력해주세요.")
        
        st.markdown("---")
        
        st.markdown("#### ✏️ 컬렉션 수정")
        
        if unique_collections:
            # 컬렉션 타입 변경 (중복 제거된 컬렉션 사용)
            type_change_collections = [c for c in unique_collections.values() if c["name"] not in ["documents", "langchain_documents"]]
            if type_change_collections:
                with st.form("change_collection_type_form"):
                    st.markdown("**🔄 컬렉션 타입 변경**")
                    
                    selected_collection = st.selectbox(
                        "타입을 변경할 컬렉션",
                        [c["name"] for c in type_change_collections],
                        key="type_change_collection"
                    )
                    
                    # 현재 컬렉션의 타입 확인
                    current_collection_info = next((c for c in type_change_collections if c["name"] == selected_collection), None)
                    current_type = "공유" if current_collection_info and current_collection_info.get("user_id") is None else "개인"
                    
                    st.info(f"현재 타입: **{current_type} 컬렉션** {'🌐' if current_type == '공유' else '👤'}")
                    
                    new_type = st.radio(
                        "새 타입 선택",
                        ["개인 컬렉션", "공유 컬렉션"],
                        help="개인 컬렉션: 나만 접근 가능\n공유 컬렉션: 모든 사용자가 접근 가능",
                        key="new_collection_type"
                    )
                    
                    # 타입 변경 안내 메시지
                    if new_type == "개인 컬렉션" and current_type == "공유":
                        st.warning("⚠️ **공유 → 개인**: 모든 사용자가 접근할 수 없게 됩니다.")
                    elif new_type == "공유 컬렉션" and current_type == "개인":
                        st.warning("⚠️ **개인 → 공유**: 모든 사용자가 접근할 수 있게 됩니다.")
                    elif new_type == current_type:
                        st.info("현재와 동일한 타입입니다.")
                    
                    if st.form_submit_button("타입 변경", type="primary"):
                        if new_type != current_type:
                            try:
                                # API 호출을 위한 타입 변환
                                api_type = "personal" if new_type == "개인 컬렉션" else "shared"
                                
                                response = chat_controller.change_collection_type(selected_collection, api_type)
                                
                                if response.get("success", False):
                                    new_type_icon = "👤" if new_type == "개인 컬렉션" else "🌐"
                                    st.success(f"✅ 컬렉션 '{selected_collection}'이 {new_type}으로 변경되었습니다. {new_type_icon}")
                                    # 컬렉션 데이터 새로고침
                                    if hasattr(chat_controller, '_collections_cache'):
                                        delattr(chat_controller, '_collections_cache')
                                    # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                                    if 'collections_data' in st.session_state:
                                        del st.session_state.collections_data
                                    # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                                    st.markdown("""
                                    <script>
                                    setTimeout(function() {
                                        window.location.reload();
                                    }, 1000);
                                    </script>
                                    """, unsafe_allow_html=True)
                                else:
                                    error_msg = response.get('error', '알 수 없는 오류')
                                    st.error(f"컬렉션 타입 변경에 실패했습니다: {error_msg}")
                            except Exception as e:
                                st.error(f"❌ 컬렉션 타입 변경 중 오류가 발생했습니다: {str(e)}")
                        else:
                            st.info("현재와 동일한 타입입니다. 변경할 필요가 없습니다.")
                
                st.markdown("---")
            
            # 컬렉션 이름 변경 (중복 제거된 컬렉션 사용)
            rename_collections = [c for c in unique_collections.values() if c["name"] not in ["documents", "langchain_documents"]]
            if rename_collections:
                with st.form("rename_collection_form"):
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
                    
                    if st.form_submit_button("이름 변경", type="primary"):
                        if new_name and new_name != old_name:
                            # Validate new collection name
                            if not re.match(r'^[a-zA-Z0-9가-힣_-]+$', new_name):
                                st.error("컬렉션 이름은 영문자, 숫자, 한글, 언더스코어(_), 하이픈(-)만 사용할 수 있습니다.")
                            else:
                                try:
                                    response = chat_controller.rename_collection(old_name, new_name)
                                    
                                    if response.get("success", False):
                                        st.success(f"✅ 컬렉션 이름이 '{old_name}'에서 '{new_name}'으로 변경되었습니다.")
                                        # 컬렉션 데이터 새로고침
                                        if hasattr(chat_controller, '_collections_cache'):
                                            delattr(chat_controller, '_collections_cache')
                                        # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                                        if 'collections_data' in st.session_state:
                                            del st.session_state.collections_data
                                        # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                                        st.markdown("""
                                        <script>
                                        setTimeout(function() {
                                            window.location.reload();
                                        }, 1000);
                                        </script>
                                        """, unsafe_allow_html=True)
                                    else:
                                        error_msg = response.get('error', '알 수 없는 오류')
                                        if "already exists" in error_msg:
                                            st.success(f"✅ 컬렉션 이름이 '{old_name}'에서 '{new_name}'으로 변경되었습니다.")
                                            # 컬렉션 데이터 새로고침
                                            if hasattr(chat_controller, '_collections_cache'):
                                                delattr(chat_controller, '_collections_cache')
                                            # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                                            if 'collections_data' in st.session_state:
                                                del st.session_state.collections_data
                                            # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                                            st.markdown("""
                                            <script>
                                            setTimeout(function() {
                                                window.location.reload();
                                            }, 1000);
                                            </script>
                                            """, unsafe_allow_html=True)
                                        elif "not found" in error_msg:
                                            st.error(f"컬렉션 '{old_name}'을 찾을 수 없습니다.")
                                        else:
                                            st.error(f"컬렉션 이름 변경에 실패했습니다: {error_msg}")
                                except Exception as e:
                                    st.error(f"❌ 컬렉션 이름 변경 중 오류가 발생했습니다: {str(e)}")
                        else:
                            st.info("새 이름을 입력해주세요.")
            else:
                st.info("이름을 변경할 수 있는 컬렉션이 없습니다.")
        else:
            st.info("컬렉션이 없습니다.")
        
        st.markdown("---")
        
        st.markdown("#### 🔄 컬렉션 전환")
        
        if unique_collections:
            # 중복 제거된 컬렉션 이름 목록 생성
            collection_names = list(unique_collections.keys())
            selected_collection = st.selectbox(
                "활성 컬렉션 선택",
                collection_names,
                index=collection_names.index(current_collection) if current_collection in collection_names else 0
            )
            
            if st.button("컬렉션 전환", type="primary"):
                if selected_collection != current_collection:
                    try:
                        response = chat_controller.switch_collection(selected_collection)
                        
                        if response.get("success", False):
                            st.success(f"✅ 컬렉션이 '{selected_collection}'로 정상 전환되었습니다.")
                            # 컬렉션 데이터 새로고침
                            if hasattr(chat_controller, '_collections_cache'):
                                delattr(chat_controller, '_collections_cache')
                            # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                            if 'collections_data' in st.session_state:
                                del st.session_state.collections_data
                            # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                            st.markdown("""
                            <script>
                            setTimeout(function() {
                                window.location.reload();
                            }, 1000);
                            </script>
                            """, unsafe_allow_html=True)
                        else:
                            error_msg = response.get('error', '알 수 없는 오류')
                            if "already selected" in error_msg or "이미 선택된" in error_msg:
                                st.success(f"✅ 컬렉션이 '{selected_collection}'로 정상 전환되었습니다.")
                                # 컬렉션 데이터 새로고침
                                if hasattr(chat_controller, '_collections_cache'):
                                    delattr(chat_controller, '_collections_cache')
                                # 세션 상태에서 컬렉션 데이터 제거하여 새로고침 강제
                                if 'collections_data' in st.session_state:
                                    del st.session_state.collections_data
                                # JavaScript를 사용한 페이지 새로고침 (무한 루프 방지)
                                st.markdown("""
                                <script>
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1000);
                                </script>
                                """, unsafe_allow_html=True)
                            else:
                                st.error(f"컬렉션 전환에 실패했습니다: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ 컬렉션 전환 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.info("이미 선택된 컬렉션입니다.")
        else:
            st.info("컬렉션이 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_session_management(chat_controller):
    """Render session management section"""
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    
    st.subheader("📋 세션 관리")
    st.write("채팅 세션을 생성, 전환, 삭제할 수 있습니다.")
    
    # Current session display
    current_session = st.session_state.get("session_id", "default")
    st.text_input("현재 세션 ID", value=current_session, disabled=True)
    
    # Session list
    st.markdown("#### 📋 세션 목록")
    
    # Import here to avoid circular imports
    from services.api_service import APIService
    api_service = APIService()
    
    # Get all sessions
    sessions_response = api_service.get_sessions()
    if sessions_response.get("success"):
        sessions = sessions_response.get("sessions", [])
        
        if sessions:
            # Session selector
            session_options = []
            session_map = {}
            
            for session_id in sessions:
                # Create display name for session
                if session_id == "default":
                    display_name = f"기본 세션 ({session_id})"
                else:
                    # Check if session has a custom name
                    session_name = st.session_state.get(f"session_name_{session_id}", "")
                    if session_name:
                        # Try to get session info to show message count
                        history_response = api_service.get_chat_history(session_id, limit=1)
                        if history_response.get("success"):
                            message_count = len(history_response.get("messages", []))
                            display_name = f"{session_name} ({message_count}개 메시지)"
                        else:
                            display_name = f"{session_name} (메시지 없음)"
                    else:
                        # Try to get session info to show message count
                        history_response = api_service.get_chat_history(session_id, limit=1)
                        if history_response.get("success"):
                            message_count = len(history_response.get("messages", []))
                            display_name = f"세션 {session_id[:8]}... ({message_count}개 메시지)"
                        else:
                            display_name = f"세션 {session_id[:8]}..."
                
                session_options.append(display_name)
                session_map[display_name] = session_id
            
            # Add current session if not in list
            if current_session not in sessions:
                session_options.insert(0, f"현재 세션 ({current_session})")
                session_map[f"현재 세션 ({current_session})"] = current_session
            
            # Find current session index
            current_index = 0
            for i, option in enumerate(session_options):
                if session_map[option] == current_session:
                    current_index = i
                    break
            
            # Session selector
            selected_display = st.selectbox(
                "세션 선택",
                session_options,
                index=current_index,
                key="session_selector"
            )
            
            if selected_display and session_map[selected_display] != current_session:
                if st.button("🔄 세션 전환", key="switch_session"):
                    try:
                        # Use ChatController to switch session and load history
                        chat_controller.switch_to_session(session_map[selected_display])
                        st.success(f"✅ 세션이 '{session_map[selected_display]}'로 전환되었습니다.")
                    except Exception as e:
                        st.error(f"❌ 세션 전환 중 오류가 발생했습니다: {str(e)}")
            
            # Session name editing
            st.markdown("#### ✏️ 세션 이름 편집")
            current_session_name = st.session_state.get(f"session_name_{current_session}", "")
            new_session_name = st.text_input(
                "세션 이름",
                value=current_session_name,
                placeholder="세션 이름을 입력하세요...",
                key=f"session_name_input_{current_session}"
            )
            
            if new_session_name != current_session_name:
                if st.button("💾 이름 저장", key="save_session_name"):
                    st.session_state[f"session_name_{current_session}"] = new_session_name
                    st.success("✅ 세션 이름이 저장되었습니다.")
            
            # Session actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("➕ 새 세션", key="new_session"):
                    try:
                        new_session_id = str(uuid.uuid4())
                        
                        # Set all session state at once to avoid infinite loop
                        st.session_state.session_id = new_session_id
                        st.session_state.messages = []  # Clear messages for new session
                        st.session_state.last_loaded_session = new_session_id  # Update last loaded session
                        st.session_state.is_new_session = True  # Mark as new session to skip existence check
                        
                        st.success("✅ 새 세션이 생성되었습니다.")
                    except Exception as e:
                        st.error(f"❌ 새 세션 생성 중 오류가 발생했습니다: {str(e)}")
            
            with col2:
                if st.button("🗑️ 세션 삭제", key="delete_session"):
                    if current_session != "default":  # Don't allow deleting default session
                        try:
                            delete_response = api_service.clear_session(current_session)
                            if delete_response.get("success"):
                                # Also remove session name from session state
                                if f"session_name_{current_session}" in st.session_state:
                                    del st.session_state[f"session_name_{current_session}"]
                                st.success("✅ 세션이 삭제되었습니다.")
                                st.session_state.session_id = "default"
                            else:
                                st.error("❌ 세션 삭제에 실패했습니다.")
                        except Exception as e:
                            st.error(f"❌ 세션 삭제 중 오류가 발생했습니다: {str(e)}")
                    else:
                        st.warning("⚠️ 기본 세션은 삭제할 수 없습니다.")
            
            with col3:
                if st.button("🔄 새로고침", key="refresh_session_list"):
                    st.info("🔄 세션 목록을 새로고침합니다...")
                    # 세션 데이터 새로고침을 위한 플래그 설정
                    st.session_state.refresh_sessions = True
            
            # All sessions delete section
            st.markdown("---")
            st.markdown("#### ⚠️ 위험한 작업")
            
            # Show session count
            non_default_sessions = [s for s in sessions if s != "default"]
            if non_default_sessions:
                st.warning(f"⚠️ **{len(non_default_sessions)}개의 세션**이 삭제 대상입니다.")
                
                # Confirmation checkbox
                confirm_delete = st.checkbox(
                    "모든 세션 삭제를 확인합니다 (기본 세션 제외)",
                    key="confirm_delete_all",
                    help="이 작업은 되돌릴 수 없습니다!"
                )
                
                if confirm_delete:
                    # Additional confirmation with session list
                    st.markdown("**삭제될 세션 목록:**")
                    for session_id in non_default_sessions:
                        session_name = st.session_state.get(f"session_name_{session_id}", "")
                        if session_name:
                            st.write(f"• {session_name} ({session_id[:8]}...)")
                        else:
                            st.write(f"• 세션 {session_id[:8]}...")
                    
                    # Final delete button
                    if st.button("💥 모든 세션 삭제", key="delete_all_sessions", type="primary"):
                        # Use ChatController to delete all sessions
                        with st.spinner("모든 세션을 삭제하는 중..."):
                            result = chat_controller.clear_all_sessions()
                        
                        if result.get("success"):
                            cleared_count = len(result.get("cleared_sessions", []))
                            
                            # Clear session names from session state
                            for session_id in result.get("cleared_sessions", []):
                                if f"session_name_{session_id}" in st.session_state:
                                    del st.session_state[f"session_name_{session_id}"]
                            
                            # Switch to default session and clear messages
                            st.session_state.session_id = "default"
                            st.session_state.messages = []
                            st.session_state.last_loaded_session = "default"
                            
                            # Show success message
                            st.success(f"✅ {cleared_count}개의 세션이 삭제되었습니다.")
                        else:
                            st.error(f"❌ 세션 삭제에 실패했습니다: {result.get('error', '알 수 없는 오류')}")
            else:
                st.info("삭제할 세션이 없습니다. (기본 세션만 존재)")
        else:
            st.info("저장된 세션이 없습니다.")
            if st.button("➕ 새 세션 생성", key="create_first_session"):
                try:
                    new_session_id = str(uuid.uuid4())
                    st.session_state.session_id = new_session_id
                    st.success("✅ 새 세션이 생성되었습니다.")
                except Exception as e:
                    st.error(f"❌ 새 세션 생성 중 오류가 발생했습니다: {str(e)}")
    else:
        st.error("세션 목록을 불러올 수 없습니다.")
        if st.button("🔄 새로고침", key="refresh_sessions"):
            st.info("🔄 세션 목록을 새로고침합니다...")
            # 세션 데이터 새로고침을 위한 플래그 설정
            st.session_state.refresh_sessions = True
    
    st.markdown('</div>', unsafe_allow_html=True)



def render_connection_status(chat_controller):
    """Render connection status section"""
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    
    st.subheader("🔗 연결 상태")
    st.write("시스템 연결 상태를 확인하고 관리할 수 있습니다.")
    
    # Connection status display
    if st.session_state.get("backend_connected", False):
        st.markdown("""
        <div class="status-card status-online">
            <h4>🟢 백엔드 서버 연결됨</h4>
            <p>시스템이 정상적으로 작동하고 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-card status-offline">
            <h4>🔴 백엔드 서버 연결 실패</h4>
            <p>서버가 실행 중인지 확인해주세요.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Connection test
    if st.button("🔄 연결 확인", key="check_connection"):
        try:
            st.session_state.backend_connected = chat_controller.check_backend_connection()
            if st.session_state.backend_connected:
                st.success("✅ 백엔드 서버에 연결되었습니다.")
            else:
                st.error("❌ 백엔드 서버에 연결할 수 없습니다.")
        except Exception as e:
            st.error(f"❌ 연결 확인 중 오류가 발생했습니다: {str(e)}")
            st.session_state.backend_connected = False
    
    # System information
    st.markdown("#### 📊 시스템 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("현재 세션", st.session_state.get("session_id", "default"))
        st.metric("메시지 수", len(st.session_state.get("messages", [])))
    
    with col2:
        st.metric("RAG 모드", st.session_state.get("rag_mode", "기본 RAG"))
        st.metric("스트리밍", "활성화" if st.session_state.get("streaming_enabled", True) else "비활성화")
    
    # Service status
    st.markdown("#### 🔧 서비스 상태")
    
    # Check various services
    services_status = []
    
    # Backend connection
    if st.session_state.get("backend_connected", False):
        services_status.append(("백엔드 API", "🟢 정상", "success"))
    else:
        services_status.append(("백엔드 API", "🔴 오프라인", "error"))
    
    # Vector DB
    try:
        collections_response = chat_controller.get_collections_response()
        if collections_response.get("success", False):
            services_status.append(("Vector DB", "🟢 정상", "success"))
        else:
            services_status.append(("Vector DB", "🟡 제한적", "warning"))
    except:
        services_status.append(("Vector DB", "🔴 오프라인", "error"))
    
    # Display service status
    for service_name, status, status_type in services_status:
        if status_type == "success":
            st.success(f"{service_name}: {status}")
        elif status_type == "warning":
            st.warning(f"{service_name}: {status}")
        else:
            st.error(f"{service_name}: {status}")
    
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
