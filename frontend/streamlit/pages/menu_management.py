"""
Menu Management Page for HAI Portal
"""
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="메뉴 관리",
    page_icon="📋",
    layout="wide"
)
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from services.api_service import APIService

def check_auth_status():
    """Check if user is authenticated"""
    if not st.session_state.get("auth_token"):
        return False
    
    # Verify token with backend
    try:
        api_service = APIService()
        result = api_service.verify_token(st.session_state.auth_token)
        return result.get("valid", False)
    except:
        return False

def check_admin_permission():
    """Check if user has admin permission"""
    user_info = st.session_state.get("user_info")
    if not user_info:
        return False
    
    # Check if user is admin (you can modify this logic based on your admin check)
    from config import ADMIN_USER_ID
    return user_info.get("id") == ADMIN_USER_ID

def get_default_menu_config():
    """Get default menu configuration"""
    return {
        "menu_items": [
            {
                "id": "main",
                "title": "채팅",
                "icon": "💬",
                "enabled": True,
                "order": 1,
                "description": "AI 채팅 기능"
            },
            {
                "id": "file_upload",
                "title": "파일 업로드",
                "icon": "📤",
                "enabled": True,
                "order": 2,
                "description": "문서 업로드 및 관리"
            },
            {
                "id": "web_search",
                "title": "웹 검색",
                "icon": "🔍",
                "enabled": True,
                "order": 3,
                "description": "웹 검색 기능"
            },
            {
                "id": "configuration",
                "title": "설정",
                "icon": "⚙️",
                "enabled": True,
                "order": 4,
                "description": "시스템 설정"
            },
            {
                "id": "accessibility_demo",
                "title": "접근성 체크 및 데모",
                "icon": "♿",
                "enabled": True,
                "order": 5,
                "description": "접근성 테스트 도구"
            },
            {
                "id": "user_management",
                "title": "사용자 관리",
                "icon": "👥",
                "enabled": True,
                "order": 6,
                "description": "사용자 계정 관리",
                "admin_only": True
            },
            {
                "id": "menu_management",
                "title": "메뉴 관리",
                "icon": "📋",
                "enabled": True,
                "order": 7,
                "description": "메뉴 설정 관리",
                "admin_only": True
            }
        ]
    }

def load_menu_config():
    """Load menu configuration from session state"""
    if "menu_config" not in st.session_state:
        st.session_state.menu_config = get_default_menu_config()
    return st.session_state.menu_config

def save_menu_config(config):
    """Save menu configuration to session state"""
    st.session_state.menu_config = config

def render_menu_list():
    """Render menu items list with management options"""
    config = load_menu_config()
    menu_items = config["menu_items"]
    
    st.markdown("### 📋 메뉴 항목 관리")
    st.write("메뉴 항목의 표시/숨김, 순서, 이름을 관리할 수 있습니다.")
    
    # Sort by order
    sorted_items = sorted(menu_items, key=lambda x: x["order"])
    
    for i, item in enumerate(sorted_items):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 1])
            
            with col1:
                st.write(f"**{item['order']}**")
            
            with col2:
                st.write(f"{item['icon']} **{item['title']}**")
                st.caption(item['description'])
                if item.get('admin_only'):
                    st.caption("🔒 관리자 전용")
            
            with col3:
                enabled = st.checkbox(
                    "표시",
                    value=item['enabled'],
                    key=f"enabled_{item['id']}",
                    help="메뉴에 표시할지 여부"
                )
                item['enabled'] = enabled
            
            with col4:
                new_order = st.number_input(
                    "순서",
                    min_value=1,
                    max_value=len(menu_items),
                    value=item['order'],
                    key=f"order_{item['id']}",
                    help="메뉴 순서 (1부터 시작)"
                )
                item['order'] = new_order
            
            with col5:
                if st.button("✏️", key=f"edit_{item['id']}", help="편집"):
                    st.session_state[f"editing_{item['id']}"] = True
                    st.rerun()
            
            st.markdown("---")
    
    # Save changes
    if st.button("💾 변경사항 저장", type="primary", use_container_width=True):
        # Update order conflicts
        orders = [item['order'] for item in menu_items]
        if len(orders) != len(set(orders)):
            st.error("순서가 중복되었습니다. 각 메뉴 항목은 고유한 순서를 가져야 합니다.")
            return
        
        save_menu_config(config)
        st.success("메뉴 설정이 저장되었습니다!")
        st.rerun()

def render_menu_edit_form(item_id):
    """Render menu item edit form"""
    config = load_menu_config()
    menu_items = config["menu_items"]
    
    item = next((item for item in menu_items if item['id'] == item_id), None)
    if not item:
        st.error("메뉴 항목을 찾을 수 없습니다.")
        return
    
    st.markdown(f"### ✏️ 메뉴 편집: {item['title']}")
    
    with st.form(f"edit_form_{item_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_title = st.text_input(
                "메뉴 제목",
                value=item['title'],
                help="사이드바에 표시될 메뉴 이름"
            )
            
            new_icon = st.text_input(
                "아이콘",
                value=item['icon'],
                help="메뉴 아이콘 (이모지)"
            )
        
        with col2:
            new_order = st.number_input(
                "순서",
                min_value=1,
                max_value=len(menu_items),
                value=item['order'],
                help="메뉴 순서"
            )
            
            new_enabled = st.checkbox(
                "표시 여부",
                value=item['enabled'],
                help="메뉴에 표시할지 여부"
            )
        
        new_description = st.text_area(
            "설명",
            value=item['description'],
            help="메뉴 설명"
        )
        
        admin_only = st.checkbox(
            "관리자 전용",
            value=item.get('admin_only', False),
            help="관리자만 볼 수 있는 메뉴"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("💾 저장", type="primary"):
                # Update item
                item['title'] = new_title
                item['icon'] = new_icon
                item['order'] = new_order
                item['enabled'] = new_enabled
                item['description'] = new_description
                item['admin_only'] = admin_only
                
                save_menu_config(config)
                del st.session_state[f"editing_{item_id}"]
                st.success("메뉴가 업데이트되었습니다!")
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ 취소"):
                del st.session_state[f"editing_{item_id}"]
                st.rerun()
        
        with col3:
            if st.form_submit_button("🗑️ 삭제", type="secondary"):
                if item_id in ['main', 'login']:  # Essential menus
                    st.error("필수 메뉴는 삭제할 수 없습니다.")
                else:
                    menu_items.remove(item)
                    save_menu_config(config)
                    del st.session_state[f"editing_{item_id}"]
                    st.success("메뉴가 삭제되었습니다!")
                    st.rerun()

def render_menu_preview():
    """Render menu preview"""
    config = load_menu_config()
    menu_items = config["menu_items"]
    
    st.markdown("### 👀 메뉴 미리보기")
    st.write("현재 설정된 메뉴가 어떻게 보일지 미리보기입니다.")
    
    # Filter enabled items and sort by order
    enabled_items = [item for item in menu_items if item['enabled']]
    sorted_items = sorted(enabled_items, key=lambda x: x['order'])
    
    # Check admin permission for admin-only items
    is_admin = check_admin_permission()
    
    with st.container():
        st.markdown("**📱 사이드바 메뉴**")
        for item in sorted_items:
            if item.get('admin_only') and not is_admin:
                continue
            
            st.markdown(f"""
            <div style="padding: 0.5rem; margin: 0.25rem 0; border-radius: 8px; background: #f8f9fa; border-left: 3px solid #6c757d;">
                <strong>{item['icon']} {item['title']}</strong>
                <br><small style="color: #6c757d;">{item['description']}</small>
            </div>
            """, unsafe_allow_html=True)

def render_menu_statistics():
    """Render menu statistics"""
    config = load_menu_config()
    menu_items = config["menu_items"]
    
    st.markdown("### 📊 메뉴 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = len(menu_items)
        st.metric("전체 메뉴", total_items)
    
    with col2:
        enabled_items = len([item for item in menu_items if item['enabled']])
        st.metric("활성 메뉴", enabled_items)
    
    with col3:
        admin_items = len([item for item in menu_items if item.get('admin_only', False)])
        st.metric("관리자 전용", admin_items)
    
    with col4:
        disabled_items = total_items - enabled_items
        st.metric("비활성 메뉴", disabled_items)

def main():
    """Main menu management page function"""
    # Check authentication
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # Check admin permission
    if not check_admin_permission():
        st.error("❌ 관리자 권한이 필요합니다.")
        st.info("이 페이지는 관리자만 접근할 수 있습니다.")
        if st.button("← 메인 페이지로 돌아가기"):
            st.session_state.current_page = "main"
            st.rerun()
        return
    
    # Modern Enterprise UI - Pure White Menu Management Theme
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
    
    /* Menu management cards */
    .menu-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .menu-card:hover {
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
        
        .menu-card {
            padding: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">📋 메뉴 관리</div>
        <div class="page-subtitle">사이드바 메뉴의 표시, 순서, 이름을 관리할 수 있습니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if editing a specific item
    editing_item = None
    for key in st.session_state.keys():
        if key.startswith("editing_") and st.session_state[key]:
            editing_item = key.replace("editing_", "")
            break
    
    if editing_item:
        render_menu_edit_form(editing_item)
    else:
        # Create tabs for different management sections
        tab1, tab2, tab3 = st.tabs(["📋 메뉴 목록", "👀 미리보기", "📊 통계"])
        
        with tab1:
            render_menu_list()
        
        with tab2:
            render_menu_preview()
        
        with tab3:
            render_menu_statistics()

if __name__ == "__main__":
    main()
