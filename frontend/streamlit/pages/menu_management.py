"""
Menu Management Page for HAI Portal
"""
import streamlit as st
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from services.api_service import APIService
from services.sidebar_management_service import sidebar_manager
from utils.helpers import UIHelpers

def check_auth_status():
    """Check if user is authenticated"""
    if not st.session_state.get("auth_token"):
        return False
    
    # Verify token with backend
    try:
        api_service = APIService(base_url="http://localhost:9502")
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
                "id": "user_management",
                "title": "사용자 관리",
                "icon": "👥",
                "enabled": True,
                "order": 5,
                "description": "사용자 계정 관리",
                "admin_only": True
            },
            {
                "id": "menu_management",
                "title": "메뉴 관리",
                "icon": "📋",
                "enabled": True,
                "order": 6,
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

def render_sidebar_management():
    """사이드바 네비게이션 관리"""
    st.markdown("### 🧭 사이드바 네비게이션 관리")
    st.write("Streamlit Navigation Sidebar의 메뉴 항목을 관리할 수 있습니다.")
    
    # 현재 사이드바 메뉴 목록
    menus = sidebar_manager.get_menus()
    
    if not menus:
        st.info("등록된 사이드바 메뉴가 없습니다.")
        return
    
    # 메뉴 목록 표시
    st.markdown("#### 📋 현재 사이드바 메뉴")
    
    for i, menu in enumerate(menus):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 1, 1])
            
            with col1:
                st.write(f"**{menu.get('order', i+1)}**")
            
            with col2:
                st.write(f"{menu.get('icon', '📄')} **{menu.get('name', '')}**")
                st.caption(menu.get('description', ''))
                st.caption(f"페이지: {menu.get('page', '')}")
            
            with col3:
                visible = st.checkbox(
                    "표시",
                    value=menu.get('visible', True),
                    key=f"sidebar_visible_{menu['id']}",
                    help="사이드바에 표시할지 여부"
                )
                if visible != menu.get('visible', True):
                    sidebar_manager.toggle_menu_visibility(menu['id'])
                    st.rerun()
            
            with col4:
                new_order = st.number_input(
                    "순서",
                    min_value=1,
                    max_value=len(menus),
                    value=menu.get('order', i+1),
                    key=f"sidebar_order_{menu['id']}",
                    help="메뉴 순서"
                )
                if new_order != menu.get('order', i+1):
                    sidebar_manager.update_menu(menu['id'], order=new_order)
                    st.rerun()
            
            with col5:
                if st.button("삭제", key=f"delete_sidebar_{menu['id']}", type="secondary"):
                    if sidebar_manager.delete_menu(menu['id']):
                        st.success("메뉴가 삭제되었습니다.")
                        st.rerun()
                    else:
                        st.error("메뉴 삭제에 실패했습니다.")
    
    st.markdown("---")
    
    # 새 메뉴 추가
    st.markdown("#### ➕ 새 메뉴 추가")
    
    with st.form("add_sidebar_menu"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("메뉴 이름", placeholder="예: 설정")
            new_page = st.text_input("페이지 경로", placeholder="예: pages/configuration.py")
        
        with col2:
            new_icon = st.text_input("아이콘", placeholder="예: ⚙️", value="📄")
            new_description = st.text_input("설명", placeholder="예: 시스템 설정")
        
        if st.form_submit_button("메뉴 추가", type="primary"):
            if new_name and new_page:
                if sidebar_manager.add_menu(
                    name=new_name,
                    page=new_page,
                    icon=new_icon,
                    description=new_description
                ):
                    st.success("새 메뉴가 추가되었습니다.")
                    st.rerun()
                else:
                    st.error("메뉴 추가에 실패했습니다.")
            else:
                st.error("메뉴 이름과 페이지 경로를 입력해주세요.")
    
    # 사이드바 미리보기
    st.markdown("---")
    st.markdown("#### 👀 사이드바 미리보기")
    
    with st.expander("현재 사이드바 모습", expanded=True):
        # 사이드바 미리보기 렌더링
        visible_menus = sidebar_manager.get_visible_menus()
        
        if visible_menus:
            st.markdown("**사이드바 메뉴:**")
            for menu in visible_menus:
                st.markdown(f"• {menu.get('icon', '📄')} {menu.get('name', '')}")
        else:
            st.info("표시되는 메뉴가 없습니다.")
    
    # 설정 내보내기/가져오기
    st.markdown("---")
    st.markdown("#### 🔧 설정 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 설정 내보내기", use_container_width=True):
            config = sidebar_manager.export_config()
            st.download_button(
                label="설정 파일 다운로드",
                data=json.dumps(config, ensure_ascii=False, indent=2),
                file_name=f"sidebar_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("설정 파일 업로드", type=['json'])
        if uploaded_file is not None:
            try:
                config = json.load(uploaded_file)
                if sidebar_manager.import_config(config):
                    st.success("설정이 성공적으로 가져와졌습니다.")
                    st.rerun()
                else:
                    st.error("설정 가져오기에 실패했습니다.")
            except Exception as e:
                st.error(f"파일 읽기 실패: {str(e)}")

def main():
    """Main menu management page function"""
    # Hide Streamlit default header elements
    UIHelpers.hide_streamlit_header()
    
    # Apply Material Design 3 Theme
    from utils.helpers import DesignThemeManager, FontManager
    theme_manager = DesignThemeManager()
    font_manager = FontManager()
    
    # Load theme from file if not already loaded
    if "theme_loaded" not in st.session_state:
        try:
            import json
            with open("data/theme_settings.json", "r", encoding="utf-8") as f:
                theme_settings = json.load(f)
                st.session_state.selected_theme = theme_settings.get("selected_theme", "gemini")
                st.session_state.theme_loaded = True
        except:
            st.session_state.selected_theme = "gemini"
            st.session_state.theme_loaded = True
    
    # Get theme from session state or default to gemini
    selected_theme = st.session_state.get("selected_theme", "gemini")
    theme_manager.apply_theme(selected_theme)
    
    # Apply font settings
    font_settings = font_manager.load_font_settings()
    font_manager.apply_font_settings(font_settings)
    
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
        tab1, tab2, tab3, tab4 = st.tabs(["📋 메뉴 목록", "🧭 사이드바 관리", "👀 미리보기", "📊 통계"])
        
        with tab1:
            render_menu_list()
        
        with tab2:
            render_sidebar_management()
        
        with tab3:
            render_menu_preview()
        
        with tab4:
            render_menu_statistics()

if __name__ == "__main__":
    main()
