"""
Collection Management Page
"""
import streamlit as st
import sys
import os
from typing import Dict, Any, List, Optional

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.chat_controller import ChatController
from components.chat_components import ChatComponents, StatusComponents

def main():
    """Collection management page"""
    # Page configuration
    st.set_page_config(
        page_title="Vector DB 컬렉션 관리",
        page_icon="🗂️",
        layout="wide"
    )
    
    # Initialize session state
    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = False
    
    # Initialize controller
    chat_controller = ChatController()
    
    # Check backend connection
    if not st.session_state.backend_connected:
        st.session_state.backend_connected = chat_controller.check_backend_connection()
    
    # Page header
    st.title("🗂️ Vector DB 컬렉션 관리")
    st.markdown("Vector Database의 컬렉션을 생성, 삭제, 이름 변경할 수 있습니다.")
    
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
        st.subheader("📚 컬렉션 목록")
        
        if not collections:
            st.info("컬렉션이 없습니다. 새 컬렉션을 생성해보세요.")
        else:
            for collection in collections:
                name = collection.get("name", "Unknown")
                doc_count = collection.get("document_count", 0)
                is_current = name == current_collection
                
                with st.container():
                    col_name, col_count, col_actions = st.columns([3, 1, 2])
                    
                    with col_name:
                        if is_current:
                            st.markdown(f"**{name}** (현재 활성) 🟢")
                        else:
                            st.markdown(f"**{name}**")
                    
                    with col_count:
                        st.markdown(f"📄 {doc_count}개")
                    
                    with col_actions:
                        if name != "documents":  # Don't allow operations on default collection
                            if st.button("삭제", key=f"delete_{name}", type="secondary"):
                                if chat_controller.delete_collection(name):
                                    st.rerun()
                        else:
                            st.markdown("기본 컬렉션")
    
    with col2:
        st.subheader("➕ 새 컬렉션 생성")
        
        with st.form("create_collection_form"):
            collection_name = st.text_input(
                "컬렉션 이름",
                placeholder="예: my_documents",
                help="컬렉션의 고유한 이름을 입력하세요"
            )
            description = st.text_area(
                "설명 (선택사항)",
                placeholder="이 컬렉션에 대한 설명을 입력하세요",
                height=100
            )
            
            if st.form_submit_button("컬렉션 생성", type="primary"):
                if collection_name:
                    # Debug: Show the request details
                    st.write(f"🔍 Debug - Creating collection: {collection_name}")
                    st.write(f"🔍 Debug - Description: {description}")
                    
                    if chat_controller.create_collection(collection_name, description):
                        st.rerun()
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
                if selected_collection != current_collection:
                    if chat_controller.switch_collection(selected_collection):
                        st.rerun()
                else:
                    st.info("이미 선택된 컬렉션입니다.")
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
                        if chat_controller.rename_collection(old_name, new_name):
                            st.rerun()
                    else:
                        st.error("새 이름을 입력하고 기존 이름과 다르게 설정해주세요.")
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

