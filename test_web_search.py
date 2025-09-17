#!/usr/bin/env python3
"""
웹 검색 기능 테스트 스크립트
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from services.web_search_service import WebSearchService

async def test_web_search():
    """웹 검색 서비스를 테스트합니다."""
    print("🔍 웹 검색 서비스 테스트 시작...")
    
    # 환경 변수 확인
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    serpapi_key = os.getenv("SERPAPI_KEY")
    
    print(f"Google API Key 설정됨: {'✅' if google_api_key else '❌'}")
    print(f"Google CSE ID 설정됨: {'✅' if google_cse_id else '❌'}")
    print(f"SerpAPI Key 설정됨: {'✅' if serpapi_key else '❌'}")
    
    if not google_api_key and not serpapi_key:
        print("❌ API 키가 설정되지 않았습니다. 환경 변수를 확인해주세요.")
        return
    
    # 웹 검색 서비스 초기화
    web_search_service = WebSearchService()
    
    # 테스트 검색어
    test_query = "Python FastAPI 웹 개발"
    print(f"\n🔍 테스트 검색어: '{test_query}'")
    
    try:
        # 웹 검색 실행
        print("검색 중...")
        results = await web_search_service.search_web(test_query, num_results=5)
        
        if results:
            print(f"✅ 검색 성공! {len(results)}개의 결과를 찾았습니다.\n")
            
            for i, result in enumerate(results, 1):
                print(f"--- 결과 {i} ---")
                print(f"제목: {result.title}")
                print(f"URL: {result.url}")
                print(f"도메인: {result.domain}")
                print(f"요약: {result.snippet[:100]}...")
                print(f"내용 길이: {len(result.content) if result.content else 0}자")
                print()
        else:
            print("❌ 검색 결과가 없습니다.")
            
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {str(e)}")

def test_search_results_formatting():
    """검색 결과 포맷팅을 테스트합니다."""
    print("\n📝 검색 결과 포맷팅 테스트...")
    
    from services.web_search_service import SearchResult
    
    # 테스트 데이터 생성
    test_results = [
        SearchResult(
            title="테스트 제목 1",
            url="https://example.com/1",
            snippet="테스트 요약 1",
            content="테스트 내용 1",
            domain="example.com"
        ),
        SearchResult(
            title="테스트 제목 2",
            url="https://test.com/2",
            snippet="테스트 요약 2",
            content="테스트 내용 2",
            domain="test.com"
        )
    ]
    
    web_search_service = WebSearchService()
    formatted_results = web_search_service.format_search_results_for_storage(test_results)
    
    print(f"✅ 포맷팅 완료! {len(formatted_results)}개의 결과를 포맷팅했습니다.")
    
    for i, result in enumerate(formatted_results, 1):
        print(f"\n--- 포맷팅된 결과 {i} ---")
        print(f"제목: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"소스: {result['source']}")
        print(f"메타데이터: {result['metadata']}")

if __name__ == "__main__":
    print("🚀 웹 검색 기능 테스트 시작")
    print("=" * 50)
    
    # 포맷팅 테스트 (API 키 없이도 실행 가능)
    test_search_results_formatting()
    
    # 실제 웹 검색 테스트 (API 키 필요)
    asyncio.run(test_web_search())
    
    print("\n✅ 테스트 완료!")
    print("\n📋 다음 단계:")
    print("1. 환경 변수 설정 (.env 파일에 API 키 추가)")
    print("2. 백엔드 서버 실행: python backend/main.py")
    print("3. 프론트엔드 실행: streamlit run frontend/streamlit/main.py")
    print("4. 웹 검색 페이지에서 기능 테스트")
