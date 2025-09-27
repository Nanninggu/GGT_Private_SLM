"""
Global Theme Manager - 모든 페이지에 일관된 테마를 적용하는 시스템
"""
import streamlit as st
from typing import Dict, Any, Optional
from .file_theme_manager import FileThemeManager
from .helpers import DesignThemeManager, UIHelpers

class GlobalThemeManager:
    """전역 테마 관리자 - 모든 페이지에서 일관된 테마 적용"""
    
    def __init__(self):
        self.file_theme_manager = FileThemeManager()
        self.theme_manager = DesignThemeManager()
        self._initialized = False
    
    def initialize_global_theme(self):
        """전역 테마 초기화 - 앱 시작 시 한 번만 호출"""
        if self._initialized:
            return
        
        # Load theme settings from file on first load
        if "theme_loaded_from_file" not in st.session_state:
            self.file_theme_manager.load_theme_to_session_state()
            st.session_state.theme_loaded_from_file = True
        
        # Initialize theme application flags
        if "applying_theme" not in st.session_state:
            st.session_state.applying_theme = False
        if "theme_rerun_count" not in st.session_state:
            st.session_state.theme_rerun_count = 0
        
        self._initialized = True
    
    def apply_global_theme(self):
        """전역 테마 적용 - 모든 페이지에서 호출"""
        # Initialize if not done yet
        self.initialize_global_theme()
        
        # Get current theme settings
        selected_theme = st.session_state.get("selected_theme", "enterprise")
        
        # Apply theme based on selection (only if not already applying)
        if not st.session_state.get("applying_theme", False):
            if selected_theme != "custom":
                # Reset theme hash when switching to predefined theme
                if "current_theme_hash" in st.session_state:
                    del st.session_state.current_theme_hash
                self.theme_manager.apply_theme(selected_theme)
            else:
                # Apply custom theme if it's selected
                custom_settings = {
                    "primary": st.session_state.get("custom_primary", "#0ea5a3"),
                    "accent": st.session_state.get("custom_accent", "#ef4444"),
                    "background": st.session_state.get("custom_background", "#f7fafc"),
                    "radius": st.session_state.get("custom_radius", 12),
                    "max_width": st.session_state.get("custom_max_width", 1200),
                    "font_size": st.session_state.get("custom_font_size", "Medium")
                }
                self.theme_manager.apply_custom_theme(custom_settings)
        
        # Hide Streamlit default header elements
        UIHelpers.hide_streamlit_header()
    
    def handle_pending_custom_theme(self):
        """대기 중인 커스텀 테마 처리"""
        if "pending_custom_theme" in st.session_state and not st.session_state.get("applying_theme", False):
            # Set flag to prevent recursive calls
            st.session_state.applying_theme = True
            
            pending_theme = st.session_state.pending_custom_theme
            
            # Create theme settings dictionary for file save
            theme_settings = {
                "selected_theme": "custom",
                "custom_primary": pending_theme.get("primary", "#0ea5a3"),
                "custom_accent": pending_theme.get("accent", "#ef4444"),
                "custom_background": pending_theme.get("background", "#f7fafc"),
                "custom_radius": pending_theme.get("radius", 12),
                "custom_max_width": pending_theme.get("max_width", 1200),
                "custom_font_size": pending_theme.get("font_size", "Medium"),
                "selected_libraries": st.session_state.get("selected_libraries", [])
            }
            
            # Save to file first
            try:
                success = self.file_theme_manager.save_theme_settings(theme_settings)
                if success:
                    # Update session state after successful file save
                    st.session_state.custom_primary = theme_settings["custom_primary"]
                    st.session_state.custom_accent = theme_settings["custom_accent"]
                    st.session_state.custom_background = theme_settings["custom_background"]
                    st.session_state.custom_radius = theme_settings["custom_radius"]
                    st.session_state.custom_max_width = theme_settings["custom_max_width"]
                    st.session_state.custom_font_size = theme_settings["custom_font_size"]
                    st.session_state.selected_theme = "custom"
                    
                    st.success("✅ 커스텀 테마가 적용되고 파일에 저장되었습니다!")
                else:
                    st.warning("⚠️ 테마가 적용되었지만 파일 저장에 실패했습니다.")
                    # Still update session state even if file save fails
                    st.session_state.custom_primary = theme_settings["custom_primary"]
                    st.session_state.custom_accent = theme_settings["custom_accent"]
                    st.session_state.custom_background = theme_settings["custom_background"]
                    st.session_state.custom_radius = theme_settings["custom_radius"]
                    st.session_state.custom_max_width = theme_settings["custom_max_width"]
                    st.session_state.custom_font_size = theme_settings["custom_font_size"]
                    st.session_state.selected_theme = "custom"
            except Exception as e:
                st.error(f"❌ 파일 저장 실패: {e}")
                # Fallback to session state only
                st.session_state.custom_primary = theme_settings["custom_primary"]
                st.session_state.custom_accent = theme_settings["custom_accent"]
                st.session_state.custom_background = theme_settings["custom_background"]
                st.session_state.custom_radius = theme_settings["custom_radius"]
                st.session_state.custom_max_width = theme_settings["custom_max_width"]
                st.session_state.custom_font_size = theme_settings["custom_font_size"]
                st.session_state.selected_theme = "custom"
                
                st.success("✅ 커스텀 테마가 적용되었습니다! (파일 저장 실패)")
            
            # Clear pending theme and reset flag
            del st.session_state.pending_custom_theme
            st.session_state.applying_theme = False
    
    def get_current_theme_info(self) -> Dict[str, Any]:
        """현재 테마 정보 반환"""
        return {
            "selected_theme": st.session_state.get("selected_theme", "enterprise"),
            "custom_primary": st.session_state.get("custom_primary", "#0ea5a3"),
            "custom_accent": st.session_state.get("custom_accent", "#ef4444"),
            "custom_background": st.session_state.get("custom_background", "#f7fafc"),
            "custom_radius": st.session_state.get("custom_radius", 12),
            "custom_max_width": st.session_state.get("custom_max_width", 1200),
            "custom_font_size": st.session_state.get("custom_font_size", "Medium"),
            "selected_libraries": st.session_state.get("selected_libraries", [])
        }
    
    def update_theme_setting(self, key: str, value: Any) -> bool:
        """테마 설정 업데이트"""
        try:
            success = self.file_theme_manager.update_theme_setting(key, value)
            if success:
                st.session_state[key] = value
            return success
        except Exception as e:
            st.error(f"❌ 테마 설정 업데이트 실패: {e}")
            return False

# 전역 인스턴스 생성
global_theme_manager = GlobalThemeManager()

def apply_global_theme():
    """전역 테마 적용 함수 - 모든 페이지에서 간단히 호출 가능"""
    global_theme_manager.apply_global_theme()

def handle_pending_custom_theme():
    """대기 중인 커스텀 테마 처리 함수"""
    global_theme_manager.handle_pending_custom_theme()

def get_current_theme_info():
    """현재 테마 정보 반환 함수"""
    return global_theme_manager.get_current_theme_info()

def update_theme_setting(key: str, value: Any) -> bool:
    """테마 설정 업데이트 함수"""
    return global_theme_manager.update_theme_setting(key, value)
