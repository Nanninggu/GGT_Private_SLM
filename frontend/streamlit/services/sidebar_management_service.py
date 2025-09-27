"""
사이드바 네비게이션 관리 서비스
Streamlit Navigation Sidebar를 동적으로 관리
"""
import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SidebarManagementService:
    """사이드바 네비게이션 관리 서비스"""
    
    def __init__(self):
        self.sidebar_data_dir = "./data/sidebar"
        self.sidebar_config_file = os.path.join(self.sidebar_data_dir, "sidebar_config.json")
        self._ensure_directories()
        self._load_sidebar_config()
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.sidebar_data_dir, exist_ok=True)
    
    def _load_sidebar_config(self):
        """사이드바 설정 로드"""
        if not os.path.exists(self.sidebar_config_file):
            # 기본 사이드바 설정 생성
            default_config = {
                "menus": [
                    {
                        "id": "main",
                        "name": "🏠 메인",
                        "page": "main.py",
                        "visible": True,
                        "order": 1,
                        "icon": "🏠",
                        "description": "메인 페이지"
                    },
                    {
                        "id": "configuration",
                        "name": "⚙️ 설정",
                        "page": "pages/configuration.py",
                        "visible": True,
                        "order": 2,
                        "icon": "⚙️",
                        "description": "시스템 설정"
                    },
                    {
                        "id": "session_management",
                        "name": "💬 세션 관리",
                        "page": "pages/session_management.py",
                        "visible": True,
                        "order": 3,
                        "icon": "💬",
                        "description": "세션 관리"
                    },
                    {
                        "id": "login",
                        "name": "🔐 로그인",
                        "page": "pages/login.py",
                        "visible": True,
                        "order": 4,
                        "icon": "🔐",
                        "description": "로그인 페이지"
                    }
                ],
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            self._save_sidebar_config(default_config)
        
        try:
            with open(self.sidebar_config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            st.error(f"사이드바 설정 로드 실패: {str(e)}")
            self.config = {"menus": [], "last_updated": datetime.now().isoformat(), "version": "1.0.0"}
    
    def _save_sidebar_config(self, config: Dict[str, Any]):
        """사이드바 설정 저장"""
        try:
            config["last_updated"] = datetime.now().isoformat()
            with open(self.sidebar_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.config = config
            return True
        except Exception as e:
            st.error(f"사이드바 설정 저장 실패: {str(e)}")
            return False
    
    def get_menus(self) -> List[Dict[str, Any]]:
        """모든 메뉴 목록 반환"""
        return self.config.get("menus", [])
    
    def get_visible_menus(self) -> List[Dict[str, Any]]:
        """보이는 메뉴 목록만 반환 (정렬됨)"""
        menus = self.config.get("menus", [])
        visible_menus = [menu for menu in menus if menu.get("visible", True)]
        return sorted(visible_menus, key=lambda x: x.get("order", 999))
    
    def add_menu(self, name: str, page: str, icon: str = "📄", description: str = "", visible: bool = True) -> bool:
        """새 메뉴 추가"""
        menus = self.config.get("menus", [])
        
        # 새 메뉴 ID 생성
        menu_id = name.lower().replace(" ", "_").replace("🏠", "main").replace("⚙️", "config").replace("💬", "session").replace("🔐", "login")
        
        # 중복 ID 체크
        existing_ids = [menu.get("id") for menu in menus]
        counter = 1
        original_id = menu_id
        while menu_id in existing_ids:
            menu_id = f"{original_id}_{counter}"
            counter += 1
        
        # 새 메뉴 생성
        new_menu = {
            "id": menu_id,
            "name": name,
            "page": page,
            "visible": visible,
            "order": len(menus) + 1,
            "icon": icon,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        
        menus.append(new_menu)
        self.config["menus"] = menus
        
        return self._save_sidebar_config(self.config)
    
    def update_menu(self, menu_id: str, **kwargs) -> bool:
        """메뉴 정보 업데이트"""
        menus = self.config.get("menus", [])
        
        for i, menu in enumerate(menus):
            if menu.get("id") == menu_id:
                # 업데이트할 필드들만 변경
                for key, value in kwargs.items():
                    if key in menu:
                        menu[key] = value
                
                menu["updated_at"] = datetime.now().isoformat()
                menus[i] = menu
                self.config["menus"] = menus
                return self._save_sidebar_config(self.config)
        
        return False
    
    def delete_menu(self, menu_id: str) -> bool:
        """메뉴 삭제"""
        menus = self.config.get("menus", [])
        original_length = len(menus)
        
        # 메뉴 삭제
        menus = [menu for menu in menus if menu.get("id") != menu_id]
        
        if len(menus) < original_length:
            self.config["menus"] = menus
            return self._save_sidebar_config(self.config)
        
        return False
    
    def toggle_menu_visibility(self, menu_id: str) -> bool:
        """메뉴 표시/숨김 토글"""
        menus = self.config.get("menus", [])
        
        for menu in menus:
            if menu.get("id") == menu_id:
                menu["visible"] = not menu.get("visible", True)
                menu["updated_at"] = datetime.now().isoformat()
                self.config["menus"] = menus
                return self._save_sidebar_config(self.config)
        
        return False
    
    def reorder_menus(self, menu_orders: List[Dict[str, int]]) -> bool:
        """메뉴 순서 변경"""
        menus = self.config.get("menus", [])
        
        # 메뉴 순서 업데이트
        for order_info in menu_orders:
            menu_id = order_info.get("id")
            new_order = order_info.get("order")
            
            for menu in menus:
                if menu.get("id") == menu_id:
                    menu["order"] = new_order
                    menu["updated_at"] = datetime.now().isoformat()
        
        self.config["menus"] = menus
        return self._save_sidebar_config(self.config)
    
    def get_menu_by_id(self, menu_id: str) -> Optional[Dict[str, Any]]:
        """ID로 메뉴 정보 조회"""
        menus = self.config.get("menus", [])
        for menu in menus:
            if menu.get("id") == menu_id:
                return menu
        return None
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        visible_menus = self.get_visible_menus()
        
        with st.sidebar:
            st.markdown("### 🧭 네비게이션")
            
            for menu in visible_menus:
                menu_name = menu.get("name", "")
                menu_page = menu.get("page", "")
                menu_icon = menu.get("icon", "📄")
                menu_description = menu.get("description", "")
                
                # 현재 페이지 확인
                current_page = st.session_state.get("current_page", "main")
                is_current = current_page in menu_page or (current_page == "main" and "main.py" in menu_page)
                
                # 메뉴 버튼 스타일
                button_type = "primary" if is_current else "secondary"
                
                if st.button(
                    menu_name,
                    key=f"sidebar_menu_{menu['id']}",
                    help=menu_description,
                    use_container_width=True,
                    type=button_type
                ):
                    # 페이지 전환
                    if menu_page:
                        if menu_page.startswith("pages/"):
                            page_name = menu_page.replace("pages/", "").replace(".py", "")
                            st.session_state.current_page = page_name
                        else:
                            st.session_state.current_page = "main"
                        st.rerun()
    
    def export_config(self) -> Dict[str, Any]:
        """설정 내보내기"""
        return self.config.copy()
    
    def import_config(self, config: Dict[str, Any]) -> bool:
        """설정 가져오기"""
        try:
            # 백업 생성
            backup_file = f"{self.sidebar_config_file}.backup"
            if os.path.exists(self.sidebar_config_file):
                import shutil
                shutil.copy2(self.sidebar_config_file, backup_file)
            
            # 새 설정 적용
            return self._save_sidebar_config(config)
        except Exception as e:
            st.error(f"설정 가져오기 실패: {str(e)}")
            return False

# 전역 인스턴스
sidebar_manager = SidebarManagementService()
