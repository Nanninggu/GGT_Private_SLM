import streamlit as st
import requests
import json
from typing import List, Dict, Any
import time

# 페이지 설정
st.set_page_config(
    page_title="웹 검색",
    page_icon="🔍",
    layout="wide"
)

# API 기본 URL
API_BASE_URL = "http://localhost:8000"

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

def search_web(query: str, num_results: int = 10) -> Dict[str, Any]:
    """웹 검색을 수행합니다."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/web-search/search",
            json={
                "query": query,
                "num_results": num_results
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
        return {"success": False, "error": str(e)}

def search_and_save_to_collection(query: str, collection_name: str, num_results: int = 10) -> Dict[str, Any]:
    """웹 검색을 수행하고 결과를 컬렉션에 저장합니다."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/web-search/search-and-save",
            json={
                "query": query,
                "num_results": num_results,
                "collection_name": collection_name,
                "auto_save": True
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"검색 및 저장 중 오류가 발생했습니다: {str(e)}")
        return {"success": False, "error": str(e)}

def get_collections(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """사용 가능한 컬렉션 목록을 가져옵니다."""
    # 세션 상태에서 컬렉션 목록 캐시 확인
    if not force_refresh and "web_search_collections" in st.session_state:
        return st.session_state.web_search_collections
    
    try:
        # Get authentication token from session state
        token = st.session_state.get("auth_token")
        if not token:
            st.error("인증 토큰이 없습니다. 로그인이 필요합니다.")
            return []
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{API_BASE_URL}/api/web-search/collections", headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            collections = data.get("collections", [])
            # 세션 상태에 캐시 저장
            st.session_state.web_search_collections = collections
            return collections
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"컬렉션 목록을 가져올 수 없습니다: {str(e)}")
        return []

def display_search_result(result: Dict[str, Any], index: int):
    """검색 결과를 표시합니다."""
    st.markdown(f"""
    <div class="search-result-card">
        <h4 style="color: #212529; margin-bottom: 1rem; font-weight: 700; font-size: 1.25rem;">
            {index + 1}. {result.get('title', '제목 없음')}
        </h4>
        <div style="margin-bottom: 1rem;">
            <p style="color: #6c757d; margin-bottom: 0.5rem; font-weight: 500; font-size: 0.9rem;">
                <strong>URL:</strong> {result.get('url', 'N/A')}
            </p>
            <p style="color: #6c757d; margin-bottom: 0.5rem; font-weight: 500; font-size: 0.9rem;">
                <strong>도메인:</strong> {result.get('domain', 'N/A')}
            </p>
        </div>
        <div style="margin-bottom: 1rem;">
            {f'<p style="color: #495057; line-height: 1.6; margin-bottom: 1rem;"><strong>요약:</strong><br>{result["snippet"]}</p>' if result.get('snippet') else ''}
            {f'<p style="color: #495057; line-height: 1.6;"><strong>내용:</strong><br>{(result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"])}</p>' if result.get('content') and result['content'] != result.get('snippet') else ''}
        </div>
        <div style="text-align: right;">
            {f'<a href="{result["url"]}" target="_blank" style="display: inline-block; padding: 0.75rem 1.5rem; background: linear-gradient(135deg, #6c757d 0%, #495057 100%); color: white; text-decoration: none; border-radius: 16px; font-weight: 600; box-shadow: 0 4px 16px rgba(0,0,0,0.08); transition: all 0.3s ease;">🔗 링크 열기</a>' if result.get('url') else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Web search page with unified design"""
    # Check authentication
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # Modern Enterprise UI - Pure White Web Search Theme
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
        box-shadow: 0 8px 40px rgba(0,0,0,0.06);
        border: 2px solid #f1f3f4;
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
    
    /* Modern Enterprise config section - Pure White */
    .config-section {
        background: #ffffff;
        padding: 3rem;
        border-radius: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.06);
        margin-bottom: 2.5rem;
        border: 2px solid #f1f3f4;
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
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 2px solid #f1f3f4;
        transition: all 0.3s ease;
    }
    
    .status-card:hover {
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border-color: #e9ecef;
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
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border: 2px solid transparent;
        font-size: 1rem;
        padding: 0.75rem 1.5rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    /* Modern Enterprise input styling */
    .stTextInput > div > div > input {
        border-radius: 16px;
        border: 2px solid #f1f3f4;
        padding: 1rem 1.25rem;
        font-size: 1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        background: #ffffff;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6c757d;
        box-shadow: 0 0 0 4px rgba(108, 117, 125, 0.1);
        background: #ffffff;
    }
    
    /* Modern Enterprise selectbox styling */
    .stSelectbox > div > div {
        border-radius: 16px;
        border: 2px solid #f1f3f4;
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
        border: 2px solid #f1f3f4;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    .stRadio > div > label:hover {
        border-color: #6c757d;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        background: #f8f9fa;
    }
    
    /* Modern Enterprise expander styling */
    .streamlit-expander {
        border: 2px solid #f1f3f4;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }
    
    /* Search result cards */
    .search-result-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 2px solid #f1f3f4;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .search-result-card:hover {
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border-color: #e9ecef;
    }
    
    /* Collection management cards */
    .collection-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 2px solid #f1f3f4;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .collection-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-color: #e9ecef;
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
        }
        
        .search-result-card, .collection-card {
            padding: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🔍 웹 검색</div>
        <div class="page-subtitle">구글 웹 검색을 수행하고 결과를 컬렉션에 저장할 수 있습니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    
    # 사이드바 - 검색 설정
    with st.sidebar:
        st.header("검색 설정")
        
        # 검색 쿼리
        query = st.text_input(
            "검색어",
            placeholder="검색할 내용을 입력하세요...",
            help="구글에서 검색할 키워드나 질문을 입력하세요."
        )
        
        # 검색 결과 수
        num_results = st.slider(
            "검색 결과 수",
            min_value=1,
            max_value=20,
            value=10,
            help="가져올 검색 결과의 개수를 선택하세요."
        )
        
        # 컬렉션 선택
        st.subheader("컬렉션 관리")
        
        # 컬렉션 목록 새로고침 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔄 새로고침", help="컬렉션 목록을 새로고침합니다."):
                # 캐시된 컬렉션 목록 삭제하고 새로고침
                if "web_search_collections" in st.session_state:
                    del st.session_state.web_search_collections
                st.rerun()
        
        with col2:
            if st.button("➕ 새 컬렉션", help="새 컬렉션을 생성합니다."):
                st.session_state.show_new_collection_form = True
                st.rerun()
        
        with col3:
            if st.button("📋 목록 보기", help="컬렉션 목록을 자세히 봅니다."):
                st.session_state.show_collection_list = not st.session_state.get("show_collection_list", False)
                st.rerun()
        
        # 컬렉션 목록 가져오기
        collections = get_collections()
        
        if collections:
            # 컬렉션 이름 목록 생성
            collection_names = [col.get("name", "") for col in collections]
            
            # 현재 선택된 컬렉션을 세션 상태에 저장
            if "selected_collection" not in st.session_state:
                st.session_state.selected_collection = collection_names[0]
            
            # 컬렉션 선택 박스
            selected_collection = st.selectbox(
                "저장할 컬렉션 선택",
                options=collection_names,
                index=collection_names.index(st.session_state.selected_collection) if st.session_state.selected_collection in collection_names else 0,
                help="검색 결과를 저장할 컬렉션을 선택하세요."
            )
            
            # 선택된 컬렉션을 세션 상태에 저장
            st.session_state.selected_collection = selected_collection
            
            # 선택된 컬렉션의 상세 정보 찾기
            selected_collection_info = next((col for col in collections if col.get("name") == selected_collection), None)
            
            if selected_collection_info:
                # 컬렉션 정보 표시
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.info(f"📁 **{selected_collection}**")
                
                with col2:
                    doc_count = selected_collection_info.get("document_count", 0)
                    st.metric("문서 수", doc_count)
                
                with col3:
                    if selected_collection_info.get("created_at"):
                        created_date = selected_collection_info["created_at"][:10]  # YYYY-MM-DD 형식
                        st.caption(f"생성일: {created_date}")
                    else:
                        st.caption("생성일: 알 수 없음")
        else:
            st.warning("사용 가능한 컬렉션이 없습니다.")
            selected_collection = None
        
        # 컬렉션 목록 상세 보기
        if st.session_state.get("show_collection_list", False) and collections:
            st.markdown("---")
            st.subheader("📋 컬렉션 목록")
            
            for i, collection in enumerate(collections, 1):
                st.markdown(f"""
                <div class="collection-card">
                    <h4 style="color: #212529; margin-bottom: 1rem; font-weight: 700; font-size: 1.1rem;">
                        📁 {collection.get('name', 'Unknown')} ({collection.get('document_count', 0)}개 문서)
                    </h4>
                    <div style="margin-bottom: 1rem;">
                        <p style="color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">
                            <strong>이름:</strong> {collection.get('name', 'Unknown')}
                        </p>
                        {f'<p style="color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;"><strong>설명:</strong> {collection["metadata"]["description"]}</p>' if collection.get('metadata', {}).get('description') else ''}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">{collection.get('document_count', 0)}</div>
                            <div style="font-size: 0.9rem; color: #6c757d; font-weight: 500;">문서 수</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.9rem; color: #6c757d; font-weight: 500;">
                                생성일: {collection['created_at'][:10] if collection.get('created_at') else '알 수 없음'}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 컬렉션 선택 및 삭제 버튼
                col_btn1, col_btn2 = st.columns([1, 1])
                
                with col_btn1:
                    if st.button(f"선택", key=f"select_collection_{i}"):
                        st.session_state.selected_collection = collection.get('name', '')
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"삭제", key=f"delete_collection_{i}", type="secondary"):
                        st.session_state.collection_to_delete = collection.get('name', '')
                        st.rerun()
        
        # 컬렉션 삭제 확인 다이얼로그
        if st.session_state.get("collection_to_delete"):
            collection_to_delete = st.session_state.collection_to_delete
            st.markdown("---")
            st.subheader("⚠️ 컬렉션 삭제 확인")
            st.warning(f"컬렉션 '{collection_to_delete}'을(를) 삭제하시겠습니까?")
            st.error("⚠️ **주의**: 이 작업은 되돌릴 수 없습니다. 컬렉션과 모든 문서가 영구적으로 삭제됩니다.")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✅ 삭제 확인", type="primary", use_container_width=True):
                    with st.spinner("컬렉션 삭제 중..."):
                        try:
                            response = requests.delete(
                                f"{API_BASE_URL}/api/collections/{collection_to_delete}"
                            )
                            
                            if response.status_code == 200:
                                response_data = response.json()
                                if response_data.get("success", False):
                                    st.success(f"컬렉션 '{collection_to_delete}'이 삭제되었습니다!")
                                    # 캐시된 컬렉션 목록 삭제하여 새로고침
                                    if "web_search_collections" in st.session_state:
                                        del st.session_state.web_search_collections
                                    # 삭제된 컬렉션이 현재 선택된 컬렉션이면 기본값으로 변경
                                    if st.session_state.get("selected_collection") == collection_to_delete:
                                        st.session_state.selected_collection = None
                                    # 삭제 확인 상태 초기화
                                    st.session_state.collection_to_delete = None
                                    st.rerun()
                                else:
                                    # Collection doesn't exist or other business logic error
                                    st.warning(f"컬렉션 '{collection_to_delete}'이 존재하지 않습니다.")
                                    st.session_state.collection_to_delete = None
                                    st.rerun()
                            elif response.status_code == 400:
                                error_data = response.json()
                                st.error(f"컬렉션 삭제 실패: {error_data.get('detail', response.text)}")
                            else:
                                error_data = response.json()
                                st.error(f"컬렉션 삭제 실패: {error_data.get('detail', response.text)}")
                        except Exception as e:
                            st.error(f"컬렉션 삭제 중 오류: {str(e)}")
            
            with col2:
                if st.button("❌ 취소", use_container_width=True):
                    st.session_state.collection_to_delete = None
                    st.rerun()
            
            with col3:
                if st.button("🔄 새로고침", use_container_width=True):
                    # 캐시된 컬렉션 목록 삭제하고 새로고침
                    if "web_search_collections" in st.session_state:
                        del st.session_state.web_search_collections
                    st.rerun()
        
        # 새 컬렉션 생성 폼 (조건부 표시)
        if st.session_state.get("show_new_collection_form", False):
            st.markdown("---")
            st.subheader("➕ 새 컬렉션 생성")
            
            # 컬렉션 타입 선택
            collection_type = st.radio(
                "컬렉션 타입",
                ["개인 컬렉션", "공유 컬렉션"],
                help="개인 컬렉션: 나만 접근 가능\n공유 컬렉션: 모든 사용자가 접근 가능",
                key="web_search_collection_type"
            )
            
            new_collection_name = st.text_input(
                "새 컬렉션 이름",
                placeholder="새 컬렉션 이름을 입력하세요...",
                help="새로운 컬렉션을 생성합니다.",
                key="new_collection_name_input"
            )
            
            # 컬렉션 타입에 따른 안내 메시지
            if collection_type == "개인 컬렉션":
                st.info("👤 **개인 컬렉션**: 나만 접근할 수 있는 개인 전용 컬렉션입니다.")
            else:
                st.warning("🌐 **공유 컬렉션**: 모든 사용자가 접근할 수 있는 공유 컬렉션입니다.")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✅ 생성", type="primary", use_container_width=True) and new_collection_name:
                    with st.spinner("컬렉션 생성 중..."):
                        try:
                            # 컬렉션 타입에 따라 다른 API 엔드포인트 사용
                            if collection_type == "개인 컬렉션":
                                api_endpoint = f"{API_BASE_URL}/api/collections/create"
                                collection_type_icon = "👤"
                                collection_type_text = "개인"
                            else:  # 공유 컬렉션
                                api_endpoint = f"{API_BASE_URL}/api/collections/create-shared"
                                collection_type_icon = "🌐"
                                collection_type_text = "공유"
                            
                            # Get authentication token from session state
                            token = st.session_state.get("auth_token")
                            if not token:
                                st.error("인증 토큰이 없습니다. 로그인이 필요합니다.")
                                return
                            
                            headers = {
                                "Authorization": f"Bearer {token}"
                            }
                            response = requests.post(
                                api_endpoint,
                                json={
                                    "collection_name": new_collection_name,
                                    "description": f"웹 검색 결과를 위한 {collection_type_text} 컬렉션: {new_collection_name}"
                                },
                                headers=headers
                            )
                            if response.status_code == 200:
                                st.success(f"✅ {collection_type_text} 컬렉션 '{new_collection_name}'이 생성되었습니다! {collection_type_icon}")
                                # 캐시된 컬렉션 목록 삭제하여 새로고침
                                if "web_search_collections" in st.session_state:
                                    del st.session_state.web_search_collections
                                # 새로 생성된 컬렉션을 선택
                                st.session_state.selected_collection = new_collection_name
                                # 폼 숨기기
                                st.session_state.show_new_collection_form = False
                                st.rerun()
                            elif response.status_code == 400:
                                # 컬렉션이 이미 존재하는 경우
                                error_data = response.json()
                                if "already exists" in error_data.get("detail", ""):
                                    st.warning(f"⚠️ {collection_type_text} 컬렉션 '{new_collection_name}'이 이미 존재합니다. 기존 컬렉션을 사용합니다. {collection_type_icon}")
                                    # 캐시된 컬렉션 목록 삭제하여 새로고침
                                    if "web_search_collections" in st.session_state:
                                        del st.session_state.web_search_collections
                                    # 기존 컬렉션을 선택
                                    st.session_state.selected_collection = new_collection_name
                                    # 폼 숨기기
                                    st.session_state.show_new_collection_form = False
                                    st.rerun()
                                else:
                                    st.error(f"컬렉션 생성 실패: {error_data.get('detail', response.text)}")
                            else:
                                st.error(f"컬렉션 생성 실패: {response.text}")
                        except Exception as e:
                            st.error(f"컬렉션 생성 중 오류: {str(e)}")
            
            with col2:
                if st.button("❌ 취소", use_container_width=True):
                    st.session_state.show_new_collection_form = False
                    st.rerun()
            
            with col3:
                if st.button("🔄 새로고침", use_container_width=True):
                    # 캐시된 컬렉션 목록 삭제하고 새로고침
                    if "web_search_collections" in st.session_state:
                        del st.session_state.web_search_collections
                    st.rerun()
    
    # 메인 검색 영역
    if query:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 검색만 하기", type="primary", use_container_width=True):
                with st.spinner("검색 중..."):
                    result = search_web(query, num_results)
                    
                    if result.get("success"):
                        st.success(f"검색 완료! {len(result.get('results', []))}개의 결과를 찾았습니다.")
                        
                        # 검색 결과 표시
                        for i, search_result in enumerate(result.get('results', [])):
                            display_search_result(search_result, i)
                    else:
                        st.error(f"검색 실패: {result.get('error', '알 수 없는 오류')}")
        
        with col2:
            if selected_collection:
                if st.button("💾 검색 후 컬렉션에 저장", type="secondary", use_container_width=True):
                    with st.spinner("검색 및 저장 중..."):
                        result = search_and_save_to_collection(query, selected_collection, num_results)
                        
                        if result.get("success"):
                            st.success(f"검색 및 저장 완료! {len(result.get('results', []))}개의 결과를 '{selected_collection}' 컬렉션에 저장했습니다.")
                            
                            # 컬렉션 목록 새로고침 (문서 수 업데이트를 위해)
                            if "web_search_collections" in st.session_state:
                                del st.session_state.web_search_collections
                            
                            # 검색 결과 표시
                            for i, search_result in enumerate(result.get('results', [])):
                                display_search_result(search_result, i)
                        else:
                            st.error(f"검색 및 저장 실패: {result.get('error', '알 수 없는 오류')}")
            else:
                st.warning("컬렉션을 선택해주세요.")
    
    # 사용법 안내
    with st.expander("📖 사용법 안내"):
        st.markdown("""
        ### 웹 검색 기능 사용법
        
        1. **검색어 입력**: 왼쪽 사이드바에서 검색할 내용을 입력하세요.
        2. **검색 결과 수 설정**: 가져올 검색 결과의 개수를 선택하세요 (1-20개).
        3. **컬렉션 관리**: 
           - **컬렉션 선택**: 검색 결과를 저장할 컬렉션을 선택하세요.
           - **새 컬렉션 생성**: 새로운 컬렉션을 생성할 수 있습니다.
           - **목록 보기**: 모든 컬렉션의 상세 정보를 확인할 수 있습니다.
           - **컬렉션 삭제**: 불필요한 컬렉션을 삭제할 수 있습니다 (주의: 되돌릴 수 없음).
           - **새로고침**: 컬렉션 목록을 최신 상태로 업데이트합니다.
        4. **검색 실행**: 
           - **검색만 하기**: 검색 결과만 확인합니다.
           - **검색 후 컬렉션에 저장**: 검색 결과를 선택한 컬렉션에 자동으로 저장합니다.
        
        ### 주요 기능
        
        - **구글 웹 검색**: Google Custom Search API를 사용한 정확한 검색
        - **실시간 컬렉션 관리**: 컬렉션 생성, 선택, 삭제, 목록 확인이 실시간으로 가능
        - **자동 새로고침**: 컬렉션 생성 후 자동으로 목록이 업데이트됩니다
        - **웹페이지 내용 추출**: 검색 결과의 실제 웹페이지 내용을 자동으로 추출
        - **컬렉션 저장**: 검색 결과를 벡터 데이터베이스에 저장하여 RAG에서 활용 가능
        - **실시간 처리**: 검색과 저장 과정을 실시간으로 모니터링
        
        ### 주의사항
        
        - 검색 결과는 최대 20개까지 가져올 수 있습니다.
        - 웹페이지 내용 추출에는 시간이 걸릴 수 있습니다.
        - 저장된 검색 결과는 채팅에서 RAG 기능을 통해 활용할 수 있습니다.
        - **컬렉션 삭제는 되돌릴 수 없으므로 신중하게 진행하세요.**
        - 기본 'langchain_documents' 컬렉션은 삭제할 수 없습니다.
        """)
    
    # 현재 컬렉션 정보
    if collections:
        st.subheader("📁 사용 가능한 컬렉션")
        col1, col2, col3 = st.columns(3)
        
        for i, collection in enumerate(collections):
            with [col1, col2, col3][i % 3]:
                st.info(f"📂 {collection}")

if __name__ == "__main__":
    main()
