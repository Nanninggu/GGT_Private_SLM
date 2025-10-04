import streamlit as st
import requests
import json
from typing import List, Dict, Any
import time
import sys
import os

# Add parent directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.helpers import UIHelpers

# API 기본 URL
API_BASE_URL = "http://localhost:9502"

def check_auth_status():
    """Check if user is authenticated"""
    if not st.session_state.get("auth_token"):
        return False
    
    # Verify token with backend
    try:
        from services.api_service import APIService
        api_service = APIService(base_url="http://localhost:9502")
        result = api_service.verify_token(st.session_state.auth_token)
        return result.get("valid", False)
    except Exception as e:
        st.error(f"인증 확인 중 오류: {str(e)}")
        return False

def search_web(query: str, num_results: int = 10, search_engine: str = "duckduckgo") -> Dict[str, Any]:
    """웹 검색을 수행합니다."""
    try:
        # Get authentication token from session state
        token = st.session_state.get("auth_token")
        if not token:
            st.error("인증 토큰이 없습니다. 로그인이 필요합니다.")
            return {"success": False, "error": "인증 토큰이 없습니다. 로그인이 필요합니다."}
        
        # 검색 엔진 이름을 API 형식으로 변환
        engine_mapping = {
            "DuckDuckGo (무료)": "duckduckgo",
            "Google Custom Search": "google",
            "SerpAPI": "serpapi"
        }
        engine = engine_mapping.get(search_engine, "duckduckgo")
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/web-search/search",
            json={
                "query": query,
                "num_results": num_results,
                "search_engine": engine
            },
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
        return {"success": False, "error": str(e)}

def search_and_save_to_collection(query: str, collection_name: str, num_results: int = 10, search_engine: str = "duckduckgo") -> Dict[str, Any]:
    """웹 검색을 수행하고 결과를 컬렉션에 저장합니다."""
    try:
        # Get authentication token from session state
        token = st.session_state.get("auth_token")
        if not token:
            st.error("인증 토큰이 없습니다. 로그인이 필요합니다.")
            return {"success": False, "error": "인증 토큰이 없습니다. 로그인이 필요합니다."}
        
        # 검색 엔진 이름을 API 형식으로 변환
        engine_mapping = {
            "DuckDuckGo (무료)": "duckduckgo",
            "Google Custom Search": "google",
            "SerpAPI": "serpapi"
        }
        engine = engine_mapping.get(search_engine, "duckduckgo")
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/web-search/search-and-save",
            json={
                "query": query,
                "num_results": num_results,
                "collection_name": collection_name,
                "auto_save": True,
                "search_engine": engine
            },
            headers=headers,
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
            # 인증 토큰이 없으면 빈 목록 반환 (에러 메시지 표시하지 않음)
            return []
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{API_BASE_URL}/api/web-search/collections", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            collections = data.get("collections", [])
            # 세션 상태에 캐시 저장
            st.session_state.web_search_collections = collections
            return collections
        return []
    except requests.exceptions.RequestException as e:
        # 에러 발생 시 빈 목록 반환 (에러 메시지 표시하지 않음)
        return []
    except Exception as e:
        # 기타 예외 발생 시 빈 목록 반환
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
    
    # Configuration 페이지로 리다이렉트 확인
    if st.session_state.get("redirect_to_configuration", False):
        # 리다이렉트 플래그 초기화
        st.session_state.redirect_to_configuration = False
        
        # Configuration 페이지로 이동
        st.markdown("""
        <script>
        // Configuration 페이지로 이동
        setTimeout(function() {
            window.location.href = '/configuration';
        }, 100);
        </script>
        """, unsafe_allow_html=True)
        
        st.info("⚙️ Configuration 페이지로 이동 중...")
        st.stop()

    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">🔍 웹 검색</div>
        <div class="page-subtitle">DuckDuckGo, Google, SerpAPI 등 다양한 검색 엔진을 사용하여 웹 검색을 수행하고 결과를 컬렉션에 저장할 수 있습니다</div>
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
            max_value=10,
            value=10,
            help="가져올 검색 결과의 개수를 선택하세요."
        )
        
        # 검색 엔진 선택
        search_engine = st.selectbox(
            "검색 엔진",
            options=["DuckDuckGo (무료)", "Google Custom Search", "SerpAPI"],
            index=0,
            help="사용할 검색 엔진을 선택하세요. DuckDuckGo는 완전 무료입니다."
        )
        
        # 검색 엔진에 따른 설명
        if search_engine == "DuckDuckGo (무료)":
            st.info("🦆 **DuckDuckGo**: 완전 무료, 개인정보 보호 중심, API 키 불필요")
        elif search_engine == "Google Custom Search":
            st.warning("🔍 **Google Custom Search**: API 키 필요, 일일 검색 제한 있음")
        elif search_engine == "SerpAPI":
            st.warning("🔍 **SerpAPI**: 유료 서비스, API 키 필요")
        
        # 컬렉션 선택
        st.subheader("컬렉션 선택")
        
        # 컬렉션 목록 새로고침 버튼
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 새로고침", help="컬렉션 목록을 새로고침합니다."):
                # 캐시된 컬렉션 목록 삭제하고 새로고침
                if "web_search_collections" in st.session_state:
                    del st.session_state.web_search_collections
                # 강제 새로고침으로 컬렉션 목록 다시 가져오기
                get_collections(force_refresh=True)
        
        with col2:
            if st.button("📋 목록 보기", help="컬렉션 목록을 자세히 봅니다."):
                st.session_state.show_collection_list = not st.session_state.get("show_collection_list", False)
        
        # 컬렉션 관리 버튼 추가
        if st.button("⚙️ 컬렉션 관리", help="컬렉션을 생성/삭제하려면 설정 페이지로 이동합니다.", use_container_width=True):
            try:
                # Streamlit 1.28.0 이상에서 사용 가능한 st.switch_page 함수 사용
                st.switch_page("pages/configuration.py")
            except AttributeError:
                # st.switch_page가 없는 경우 JavaScript를 사용한 리다이렉트
                st.markdown("""
                <script>
                // Configuration 페이지로 이동
                setTimeout(function() {
                    window.location.href = '/configuration';
                }, 100);
                </script>
                """, unsafe_allow_html=True)
                
                # 세션 상태에 페이지 이동 플래그 설정
                st.session_state.redirect_to_configuration = True
                st.session_state.current_page = "configuration"
                st.rerun()
        
        # 컬렉션 목록 가져오기 (강제 새로고침)
        collections = get_collections(force_refresh=True)
        
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
            # 인증 토큰이 있는지 확인
            if st.session_state.get("auth_token"):
                st.info("📝 사용 가능한 컬렉션이 없습니다.")
                st.info("💡 **새 컬렉션을 생성하려면**: 위의 '컬렉션 관리' 버튼을 클릭하여 설정 페이지로 이동하세요.")
            else:
                st.warning("🔐 컬렉션을 사용하려면 로그인이 필요합니다.")
            selected_collection = None
        
        # 컬렉션 목록 간단 보기
        if st.session_state.get("show_collection_list", False) and collections:
            st.markdown("---")
            st.subheader("📋 컬렉션 목록")
            
            for i, collection in enumerate(collections, 1):
                # Check if collection is shared
                is_shared = collection.get('is_shared', False)
                collection_icon = "🌐" if is_shared else "👤"
                collection_type = "공유" if is_shared else "개인"
                
                col_info, col_select = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"""
                    <div style="padding: 0.5rem; border-radius: 8px; background-color: #f8f9fa; margin-bottom: 0.5rem;">
                        <strong>{collection_icon} {collection.get('name', 'Unknown')}</strong> 
                        ({collection.get('document_count', 0)}개 문서) - {collection_type} 컬렉션
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_select:
                    if st.button(f"선택", key=f"select_collection_{i}"):
                        st.session_state.selected_collection = collection.get('name', '')
                        st.rerun()
        
    
    # 메인 검색 영역
    if query:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 검색만 하기", type="primary", use_container_width=True):
                with st.spinner(f"{search_engine}로 검색 중..."):
                    result = search_web(query, num_results, search_engine)
                    
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
                    with st.spinner(f"{search_engine}로 검색 및 저장 중..."):
                        result = search_and_save_to_collection(query, selected_collection, num_results, search_engine)
                        
                        if result.get("success"):
                            st.success(f"검색 및 저장 완료! {len(result.get('results', []))}개의 결과를 '{selected_collection}' 컬렉션에 저장했습니다.")
                            
                            # 컬렉션 목록 새로고침 (문서 수 업데이트를 위해)
                            if "web_search_collections" in st.session_state:
                                del st.session_state.web_search_collections
                            
                            # UI 자동 새로고침을 위해 st.rerun() 호출
                            st.rerun()
                            
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
        2. **검색 엔진 선택**: 사용할 검색 엔진을 선택하세요.
           - **DuckDuckGo (무료)**: 완전 무료, 개인정보 보호 중심, API 키 불필요
           - **Google Custom Search**: API 키 필요, 일일 검색 제한 있음
           - **SerpAPI**: 유료 서비스, API 키 필요
        3. **검색 결과 수 설정**: 가져올 검색 결과의 개수를 선택하세요 (1-20개).
        4. **컬렉션 선택**: 
           - **컬렉션 선택**: 검색 결과를 저장할 컬렉션을 선택하세요.
           - **목록 보기**: 모든 컬렉션의 상세 정보를 확인할 수 있습니다.
           - **새로고침**: 컬렉션 목록을 최신 상태로 업데이트합니다.
           - **컬렉션 관리**: 컬렉션 생성/삭제는 설정 페이지에서 가능합니다.
        5. **검색 실행**: 
           - **검색만 하기**: 검색 결과만 확인합니다.
           - **검색 후 컬렉션에 저장**: 검색 결과를 선택한 컬렉션에 자동으로 저장합니다.
        
        ### 주요 기능
        
        - **다양한 검색 엔진**: DuckDuckGo, Google Custom Search, SerpAPI 지원
        - **무료 검색 옵션**: DuckDuckGo를 사용하면 API 키 없이도 무료로 검색 가능
        - **컬렉션 선택**: 기존 컬렉션 중에서 검색 결과를 저장할 컬렉션을 선택
        - **통합 관리**: 컬렉션 생성/삭제는 설정 페이지에서 통합 관리
        - **웹페이지 내용 추출**: 검색 결과의 실제 웹페이지 내용을 자동으로 추출
        - **컬렉션 저장**: 검색 결과를 벡터 데이터베이스에 저장하여 RAG에서 활용 가능
        - **실시간 처리**: 검색과 저장 과정을 실시간으로 모니터링
        
        ### 주의사항
        
        - 검색 결과는 최대 20개까지 가져올 수 있습니다.
        - 웹페이지 내용 추출에는 시간이 걸릴 수 있습니다.
        - 저장된 검색 결과는 채팅에서 RAG 기능을 통해 활용할 수 있습니다.
        - **컬렉션 관리**: 컬렉션 생성/삭제는 설정 페이지에서 안전하게 관리할 수 있습니다.
        """)
    
    # 현재 컬렉션 정보 (최신 데이터로 강제 새로고침)
    latest_collections = get_collections(force_refresh=True)
    if latest_collections:
        st.subheader("📁 사용 가능한 컬렉션")
        col1, col2, col3 = st.columns(3)
        
        for i, collection in enumerate(latest_collections):
            with [col1, col2, col3][i % 3]:
                # 컬렉션 정보를 사용자 친화적으로 표시
                collection_name = collection.get('name', 'Unknown')
                document_count = collection.get('document_count', 0)
                description = collection.get('metadata', {}).get('description', '설명 없음')
                is_shared = collection.get('is_shared', False)
                collection_icon = "🌐" if is_shared else "👤"
                collection_type = "공유" if is_shared else "개인"
                
                st.markdown(f"""
                <div class="collection-card">
                    <h4 style="color: #212529; margin-bottom: 0.5rem; font-weight: 700; font-size: 1rem;">
                        {collection_icon} {collection_name}
                    </h4>
                    <p style="color: #6c757d; margin-bottom: 0.5rem; font-size: 0.9rem;">
                        <strong>타입:</strong> {collection_type} 컬렉션
                    </p>
                    <p style="color: #6c757d; margin-bottom: 0.5rem; font-size: 0.9rem;">
                        <strong>문서 수:</strong> {document_count}개
                    </p>
                    <p style="color: #6c757d; margin-bottom: 0; font-size: 0.85rem; line-height: 1.3;">
                        {description}
                    </p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
