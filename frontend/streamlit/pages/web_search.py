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

def get_collections() -> List[str]:
    """사용 가능한 컬렉션 목록을 가져옵니다."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/web-search/collections")
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return [col.get("name", "") for col in data.get("collections", [])]
        return []
    except requests.exceptions.RequestException:
        return []

def display_search_result(result: Dict[str, Any], index: int):
    """검색 결과를 표시합니다."""
    with st.expander(f"**{index + 1}. {result.get('title', '제목 없음')}**", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**URL:** {result.get('url', 'N/A')}")
            st.write(f"**도메인:** {result.get('domain', 'N/A')}")
            
            if result.get('snippet'):
                st.write("**요약:**")
                st.write(result['snippet'])
            
            if result.get('content') and result['content'] != result.get('snippet'):
                st.write("**내용:**")
                st.write(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
        
        with col2:
            if result.get('url'):
                st.link_button("🔗 링크 열기", result['url'])

def main():
    st.title("🔍 웹 검색 및 컬렉션 저장")
    st.markdown("구글 웹 검색을 수행하고 결과를 컬렉션에 저장할 수 있습니다.")
    
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
        
        # 컬렉션 목록 새로고침
        if st.button("🔄 컬렉션 목록 새로고침"):
            st.rerun()
        
        collections = get_collections()
        
        if collections:
            selected_collection = st.selectbox(
                "저장할 컬렉션 선택",
                options=collections,
                help="검색 결과를 저장할 컬렉션을 선택하세요."
            )
        else:
            st.warning("사용 가능한 컬렉션이 없습니다.")
            selected_collection = None
        
        # 새 컬렉션 생성
        with st.expander("새 컬렉션 생성"):
            new_collection_name = st.text_input(
                "새 컬렉션 이름",
                placeholder="새 컬렉션 이름을 입력하세요...",
                help="새로운 컬렉션을 생성합니다."
            )
            
            if st.button("컬렉션 생성") and new_collection_name:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/collections/create",
                        json={
                            "collection_name": new_collection_name,
                            "description": f"웹 검색 결과를 위한 컬렉션: {new_collection_name}"
                        }
                    )
                    if response.status_code == 200:
                        st.success(f"컬렉션 '{new_collection_name}'이 생성되었습니다!")
                        st.rerun()
                    else:
                        st.error(f"컬렉션 생성 실패: {response.text}")
                except Exception as e:
                    st.error(f"컬렉션 생성 중 오류: {str(e)}")
    
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
        3. **컬렉션 선택**: 검색 결과를 저장할 컬렉션을 선택하세요.
        4. **검색 실행**: 
           - **검색만 하기**: 검색 결과만 확인합니다.
           - **검색 후 컬렉션에 저장**: 검색 결과를 선택한 컬렉션에 자동으로 저장합니다.
        
        ### 주요 기능
        
        - **구글 웹 검색**: Google Custom Search API를 사용한 정확한 검색
        - **웹페이지 내용 추출**: 검색 결과의 실제 웹페이지 내용을 자동으로 추출
        - **컬렉션 저장**: 검색 결과를 벡터 데이터베이스에 저장하여 RAG에서 활용 가능
        - **실시간 처리**: 검색과 저장 과정을 실시간으로 모니터링
        
        ### 주의사항
        
        - 검색 결과는 최대 20개까지 가져올 수 있습니다.
        - 웹페이지 내용 추출에는 시간이 걸릴 수 있습니다.
        - 저장된 검색 결과는 채팅에서 RAG 기능을 통해 활용할 수 있습니다.
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
