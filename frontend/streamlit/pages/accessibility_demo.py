"""
Accessibility Demo Page for HAI Portal
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.chat_components import ChatComponents
from services.api_service import APIService

# Page configuration is handled in main.py

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
    """Accessibility demo page with unified design"""
    # Check authentication
    if not check_auth_status():
        st.warning("로그인이 필요합니다.")
        if st.button("로그인 페이지로 이동"):
            st.session_state.current_page = "login"
            st.rerun()
        return
    
    # HAI Portal styling
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
    
    /* Adjust main content padding */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .page-header {
        background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .page-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .page-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    .config-section {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #8B5CF6;
        margin-bottom: 1rem;
    }
    
    .status-online {
        border-left-color: #10B981;
        background: #f0fdf4;
    }
    
    .status-offline {
        border-left-color: #EF4444;
        background: #fef2f2;
    }
    </style>
    """, unsafe_allow_html=True)

    # Page header
    st.markdown("""
    <div class="page-header">
        <div class="page-title">♿ 접근성 데모</div>
        <div class="page-subtitle">접근성 표준에 따른 UI/UX 기능을 테스트하고 데모할 수 있습니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    
    # Inject accessibility scripts
    ChatComponents._inject_accessibility_scripts()
    
    # Create tabs for different demo sections
    tab1, tab2, tab3, tab4 = st.tabs(["📋 신뢰도 표시", "📊 정확도 측정", "🔍 시스템 상태", "🎯 고급 정확도 측정"])
    
    with tab1:
        # Demo explanation
        st.markdown("""
        ## 📋 답변 신뢰도 표시 기능 테스트
        
        이 페이지는 채팅 답변의 신뢰도를 시각적으로 표시하는 기능을 테스트합니다.
        
        ### 🎯 구현된 기능:
        
        1. **답변 신뢰도 점수**
           - 0-100% 범위의 유사도 점수 표시
           - 색상 코딩으로 직관적인 신뢰도 표시
           - 진행률 바로 시각적 표현
        
        2. **신뢰도 등급 표시**
           - 🟢 매우 높음 (80% 이상): 녹색
           - 🟡 높음 (60-79%): 노란색  
           - 🟠 보통 (40-59%): 주황색
           - 🔴 낮음 (40% 미만): 빨간색
        
        3. **깔끔한 UI**
           - 참고문서 목록 제거로 간소화
           - 답변 품질에 집중
           - 시각적 피드백 강화
        
        4. **접근성 지원**
           - 색상뿐만 아니라 텍스트로도 신뢰도 표시
           - 스크린 리더 호환성
           - 명확한 상태 표시
        """)
    
        st.markdown("---")
        
        # Demo chat message with sources
        st.subheader("📝 데모 채팅 메시지")
        
        # Sample message with context
        demo_message = {
            "role": "assistant",
            "content": """
            안녕하세요! 저는 HAI Portal의 AI 어시스턴트입니다. 
            
            접근성 표준에 따라 구현된 참조 출처 기능을 테스트해보세요. 
            아래의 참조 출처 목록을 키보드나 마우스로 조작할 수 있습니다.
            
            **키보드 사용법:**
            - Tab 키로 요소 간 이동
            - Enter 또는 Space 키로 확장/축소
            - 화살표 키로 세부 항목 탐색
            """,
            "context": [],
            "metadata": {
                "model": "gpt-4",
                "timestamp": datetime.now().isoformat(),
                "rag_mode": "LangChain RAG",
                "similarity": 0.85,  # High similarity score for demo
                "context_count": 3,
                "test_mode": True
            },
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        # Render the demo message
        ChatComponents.render_message(demo_message)
        
        st.markdown("---")
        
        # Testing instructions
        st.subheader("🧪 테스트 방법")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **👀 시각적 테스트:**
            1. 답변 아래의 신뢰도 점수 확인
            2. 색상 코딩이 올바른지 확인
            3. 진행률 바가 정확한지 확인
            4. 이모지와 텍스트 표시 확인
            """)
        
        with col2:
            st.markdown("""
            **♿ 접근성 테스트:**
            1. 스크린 리더로 신뢰도 정보 읽기
            2. 색상에 의존하지 않는 정보 전달 확인
            3. 키보드 네비게이션으로 접근 가능한지 확인
            4. 명확한 텍스트 설명 확인
            """)
        
        # Accessibility checklist
        st.subheader("✅ 접근성 체크리스트")
        
        checklist_items = [
            "신뢰도 점수가 정확하게 표시되는가?",
            "색상 코딩이 직관적인가?",
            "진행률 바가 올바른가?",
            "텍스트 설명이 명확한가?",
            "스크린 리더가 신뢰도 정보를 읽을 수 있는가?",
            "색상에 의존하지 않는 정보 전달이 가능한가?",
            "이모지와 텍스트가 조화롭게 표시되는가?",
            "전체적으로 깔끔하고 직관적인가?"
        ]
        
        for i, item in enumerate(checklist_items, 1):
            st.checkbox(f"{i}. {item}", key=f"checklist_{i}")
    
    with tab2:
        st.markdown("""
        ## 📊 정확도 측정 기능
        
        RAG 시스템의 정확도를 측정하고 분석할 수 있는 기능입니다.
        
        ### 🎯 측정 가능한 메트릭:
        
        1. **유사도 점수 (Similarity Score)**
           - 벡터 검색에서 반환되는 유사도 점수
           - 0-1 범위의 정규화된 값
        
        2. **컨텍스트 관련성 (Context Relevance)**
           - 검색된 문서가 질문과 얼마나 관련있는지
           - 평균 유사도 점수 기반
        
        3. **답변 품질 (Answer Quality)**
           - 생성된 답변의 품질 평가
           - 길이, 구조, 언어 품질 등 고려
        
        4. **전체 정확도 (Overall Accuracy)**
           - 여러 메트릭의 가중 평균
           - 시스템의 전반적인 성능 지표
        
        5. **신뢰도 (Confidence)**
           - 시스템이 답변에 대해 가지는 신뢰도
           - 컨텍스트 가용성, 유사도 등 고려
        """)
        
        st.markdown("---")
        
        # Single query accuracy measurement
        st.subheader("🔍 단일 질문 정확도 측정")
        
        with st.form("accuracy_form"):
            query = st.text_area(
                "질문을 입력하세요:",
                value="인공지능이란 무엇인가요?",
                help="정확도를 측정할 질문을 입력하세요."
            )
            
            expected_answer = st.text_area(
                "예상 답변 (선택사항):",
                value="인공지능은 인간의 지능을 모방하여 학습, 추론, 문제해결 등의 능력을 가진 컴퓨터 시스템입니다.",
                help="정확도 비교를 위한 예상 답변을 입력하세요."
            )
            
            submitted = st.form_submit_button("정확도 측정", use_container_width=True)
            
            if submitted:
                if query.strip():
                    with st.spinner("정확도를 측정하는 중..."):
                        try:
                            api_service = APIService()
                            result = api_service.measure_query_accuracy(query, expected_answer)
                            
                            if result.get("success"):
                                accuracy_data = result.get("result", {})
                                
                                # Display results
                                st.success("정확도 측정이 완료되었습니다!")
                                
                                # Create columns for metrics
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric(
                                        "전체 정확도",
                                        f"{accuracy_data.get('overall_accuracy', 0):.1%}",
                                        help="여러 메트릭의 가중 평균"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "컨텍스트 관련성",
                                        f"{accuracy_data.get('context_relevance', 0):.1%}",
                                        help="검색된 문서의 관련성"
                                    )
                                
                                with col3:
                                    st.metric(
                                        "답변 품질",
                                        f"{accuracy_data.get('answer_quality', 0):.1%}",
                                        help="생성된 답변의 품질"
                                    )
                                
                                with col4:
                                    st.metric(
                                        "신뢰도",
                                        f"{accuracy_data.get('confidence', 0):.1%}",
                                        help="시스템의 신뢰도"
                                    )
                                
                                # Additional metrics
                                st.markdown("### 📈 상세 메트릭")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**응답 정보:**")
                                    st.write(f"- 응답 시간: {accuracy_data.get('response_time', 0):.2f}초")
                                    st.write(f"- 컨텍스트 수: {accuracy_data.get('context_count', 0)}개")
                                    st.write(f"- 평균 유사도: {accuracy_data.get('average_similarity', 0):.3f}")
                                    st.write(f"- 폴백 모드: {'사용됨' if accuracy_data.get('fallback_mode', False) else '사용 안됨'}")
                                
                                with col2:
                                    st.markdown("**시스템 상태:**")
                                    st.write(f"- 성공 여부: {'성공' if accuracy_data.get('success', False) else '실패'}")
                                    st.write(f"- 컨텍스트 파일: {len(accuracy_data.get('context_files', []))}개")
                                    if accuracy_data.get('similarity_scores'):
                                        st.write(f"- 유사도 점수: {[f'{s:.3f}' for s in accuracy_data['similarity_scores']]}")
                                
                                # Display response
                                if accuracy_data.get('response'):
                                    st.markdown("### 💬 생성된 답변")
                                    st.text_area("답변 내용", accuracy_data['response'], height=200, disabled=True)
                                
                                # Expected answer comparison
                                if expected_answer and accuracy_data.get('similarity_to_expected'):
                                    st.markdown("### 🎯 예상 답변과의 유사도")
                                    similarity_to_expected = accuracy_data.get('similarity_to_expected', 0)
                                    st.metric(
                                        "유사도",
                                        f"{similarity_to_expected:.1%}",
                                        help="생성된 답변과 예상 답변 간의 유사도"
                                    )
                                
                            else:
                                st.error(f"정확도 측정 실패: {result.get('error', '알 수 없는 오류')}")
                        
                        except Exception as e:
                            st.error(f"정확도 측정 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.warning("질문을 입력해주세요.")
        
        st.markdown("---")
        
        # Test suite
        st.subheader("🧪 정확도 테스트 스위트")
        
        if st.button("샘플 테스트 실행", use_container_width=True):
            with st.spinner("샘플 테스트를 실행하는 중..."):
                try:
                    api_service = APIService()
                    result = api_service.run_accuracy_test_suite()
                    
                    if result.get("success"):
                        test_data = result.get("result", {})
                        aggregate = test_data.get("aggregate_metrics", {})
                        
                        st.success("테스트 스위트가 완료되었습니다!")
                        
                        # Display aggregate metrics
                        st.markdown("### 📊 전체 테스트 결과")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "성공률",
                                f"{aggregate.get('success_rate', 0):.1%}",
                                help="성공한 테스트의 비율"
                            )
                        
                        with col2:
                            st.metric(
                                "평균 정확도",
                                f"{aggregate.get('average_accuracy', 0):.1%}",
                                help="전체 테스트의 평균 정확도"
                            )
                        
                        with col3:
                            st.metric(
                                "평균 응답 시간",
                                f"{aggregate.get('average_response_time', 0):.2f}초",
                                help="평균 응답 시간"
                            )
                        
                        with col4:
                            st.metric(
                                "평균 신뢰도",
                                f"{aggregate.get('average_confidence', 0):.1%}",
                                help="평균 신뢰도"
                            )
                        
                        # Accuracy distribution
                        st.markdown("### 📈 정확도 분포")
                        distribution = aggregate.get('accuracy_distribution', {})
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("높음 (80% 이상)", distribution.get('high', 0))
                        
                        with col2:
                            st.metric("보통 (50-79%)", distribution.get('medium', 0))
                        
                        with col3:
                            st.metric("낮음 (50% 미만)", distribution.get('low', 0))
                        
                        # Test details
                        st.markdown("### 📋 개별 테스트 결과")
                        test_results = test_data.get("test_suite_results", [])
                        
                        for i, test_result in enumerate(test_results, 1):
                            with st.expander(f"테스트 {i}: {test_result.get('query', '')[:50]}..."):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**정확도:** {test_result.get('overall_accuracy', 0):.1%}")
                                    st.write(f"**응답 시간:** {test_result.get('response_time', 0):.2f}초")
                                    st.write(f"**성공 여부:** {'성공' if test_result.get('success', False) else '실패'}")
                                
                                with col2:
                                    st.write(f"**컨텍스트 관련성:** {test_result.get('context_relevance', 0):.1%}")
                                    st.write(f"**답변 품질:** {test_result.get('answer_quality', 0):.1%}")
                                    st.write(f"**신뢰도:** {test_result.get('confidence', 0):.1%}")
                                
                                if test_result.get('response'):
                                    st.text_area("생성된 답변", test_result['response'], height=100, disabled=True)
                    
                    else:
                        st.error(f"테스트 스위트 실행 실패: {result.get('error', '알 수 없는 오류')}")
                
                except Exception as e:
                    st.error(f"테스트 스위트 실행 중 오류가 발생했습니다: {str(e)}")
    
    with tab3:
        st.markdown("""
        ## 🔍 시스템 상태 모니터링
        
        RAG 시스템의 전반적인 상태와 성능을 모니터링할 수 있습니다.
        
        ### 📊 모니터링 항목:
        
        1. **문서 데이터베이스 상태**
           - 총 문서 수
           - 컬렉션 정보
           - 데이터베이스 연결 상태
        
        2. **시스템 성능**
           - 응답 시간
           - 메모리 사용량
           - 서비스 상태
        
        3. **정확도 지표**
           - 평균 정확도
           - 신뢰도 점수
           - 오류율
        """)
        
        st.markdown("---")
        
        # System health check
        st.subheader("🏥 시스템 상태 확인")
        
        if st.button("시스템 상태 확인", use_container_width=True):
            with st.spinner("시스템 상태를 확인하는 중..."):
                try:
                    api_service = APIService()
                    result = api_service.get_system_health()
                    
                    if result.get("success"):
                        health_data = result.get("result", {})
                        
                        st.success("시스템 상태 확인이 완료되었습니다!")
                        
                        # Document count
                        st.markdown("### 📚 문서 데이터베이스")
                        doc_count = health_data.get("document_count", 0)
                        st.metric("총 문서 수", doc_count)
                        
                        # Collections info
                        collections = health_data.get("collections", [])
                        if collections:
                            st.markdown("#### 컬렉션 정보")
                            for collection in collections:
                                st.write(f"- **{collection.get('name', 'Unknown')}**: {collection.get('document_count', 0)}개 문서")
                        
                        # Test query result
                        test_result = health_data.get("test_query_result", {})
                        if test_result:
                            st.markdown("### 🧪 테스트 쿼리 결과")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric(
                                    "응답 시간",
                                    f"{test_result.get('response_time', 0):.2f}초"
                                )
                            
                            with col2:
                                st.metric(
                                    "정확도",
                                    f"{test_result.get('overall_accuracy', 0):.1%}"
                                )
                            
                            with col3:
                                st.metric(
                                    "신뢰도",
                                    f"{test_result.get('confidence', 0):.1%}"
                                )
                            
                            if test_result.get('response'):
                                st.text_area("테스트 응답", test_result['response'], height=100, disabled=True)
                    
                    else:
                        st.error(f"시스템 상태 확인 실패: {result.get('error', '알 수 없는 오류')}")
                
                except Exception as e:
                    st.error(f"시스템 상태 확인 중 오류가 발생했습니다: {str(e)}")
    
    with tab4:
        st.markdown("""
        ## 🎯 고급 정확도 측정
        
        RAG 시스템의 정확도를 컬렉션별로 측정하고 분석할 수 있는 고급 기능입니다.
        
        ### 🚀 주요 기능:
        
        1. **컬렉션별 정확도 측정**
           - 다양한 컬렉션에서 정확도 비교
           - 컬렉션 전환 및 실시간 측정
        
        2. **단일 질문 정확도 측정**
           - 개별 질문에 대한 상세 분석
           - 예상 답변과의 유사도 비교
        
        3. **테스트 스위트 실행**
           - 여러 질문에 대한 종합 테스트
           - 정확도 분포 및 성능 분석
        
        4. **시스템 상태 모니터링**
           - 실시간 시스템 상태 확인
           - 문서 데이터베이스 상태 점검
        """)
        
        # Import here to avoid circular imports
        from controllers.chat_controller import ChatController
        chat_controller = ChatController()
        
        # Create sub-tabs for different accuracy measurement features
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🔍 단일 질문 측정", "🧪 테스트 스위트", "📈 시스템 상태"])
        
        with sub_tab1:
            st.markdown("### 🔍 단일 질문 정확도 측정")
            st.write("개별 질문에 대한 RAG 시스템의 정확도를 측정합니다.")
            
            # Collection selection section
            st.markdown("#### 📚 컬렉션 선택")
            
            # Get current collections
            collections_response = chat_controller.get_collections_response()
            if collections_response.get("success", False):
                collections = collections_response.get("collections", [])
                current_collection = collections_response.get("current_collection", "documents")
                
                # Remove duplicates and create collection options
                unique_collections = {}
                for collection in collections:
                    name = collection.get("name", "Unknown")
                    if name not in unique_collections:
                        unique_collections[name] = collection
                    else:
                        unique_collections[name]["document_count"] += collection.get("document_count", 0)
                
                # Display current collection
                st.info(f"현재 활성 컬렉션: **{current_collection}** ({unique_collections.get(current_collection, {}).get('document_count', 0)}개 문서)")
                
                # Collection selector
                collection_names = list(unique_collections.keys())
                selected_collection = st.selectbox(
                    "측정할 컬렉션 선택:",
                    collection_names,
                    index=collection_names.index(current_collection) if current_collection in collection_names else 0,
                    help="정확도 측정에 사용할 컬렉션을 선택하세요."
                )
                
                # Show collection info
                if selected_collection in unique_collections:
                    collection_info = unique_collections[selected_collection]
                    st.write(f"선택된 컬렉션: **{selected_collection}** ({collection_info.get('document_count', 0)}개 문서)")
                    
                    # Switch collection if different from current
                    if selected_collection != current_collection:
                        if st.button("🔄 컬렉션 전환", key="switch_collection_for_accuracy"):
                            try:
                                switch_response = chat_controller.switch_collection(selected_collection)
                                if switch_response.get("success", False):
                                    st.success(f"✅ 컬렉션이 '{selected_collection}'로 전환되었습니다.")
                                    st.rerun()
                                else:
                                    st.error(f"❌ 컬렉션 전환 실패: {switch_response.get('error', '알 수 없는 오류')}")
                            except Exception as e:
                                st.error(f"❌ 컬렉션 전환 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error(f"❌ 컬렉션 목록을 가져올 수 없습니다: {collections_response.get('error', '알 수 없는 오류')}")
                selected_collection = "documents"  # Fallback to default
            
            st.markdown("---")
            
            with st.form("single_accuracy_form"):
                query = st.text_area(
                    "질문을 입력하세요:",
                    value="근로기준법에 대해 설명해주세요.",
                    help="정확도를 측정할 질문을 입력하세요.",
                    height=100
                )
                
                expected_answer = st.text_area(
                    "예상 답변 (선택사항):",
                    value="근로기준법은 근로자의 기본적 권리를 보장하고 근로조건의 기준을 정한 법률입니다.",
                    help="정확도 비교를 위한 예상 답변을 입력하세요.",
                    height=100
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    submitted = st.form_submit_button("정확도 측정", use_container_width=True, type="primary")
                with col2:
                    if st.form_submit_button("샘플 질문 사용", use_container_width=True):
                        query = "머신러닝과 딥러닝의 차이점은 무엇인가요?"
                        expected_answer = "머신러닝은 데이터로부터 패턴을 학습하는 알고리즘의 총칭이고, 딥러닝은 신경망을 사용하는 머신러닝의 한 분야입니다."
                
                if submitted:
                    if query.strip():
                        with st.spinner("정확도를 측정하는 중..."):
                            try:
                                api_service = APIService()
                                result = api_service.measure_query_accuracy(query, expected_answer)
                                
                                if result.get("success"):
                                    accuracy_data = result.get("result", {})
                                    
                                    # Display success message
                                    st.success("✅ 정확도 측정이 완료되었습니다!")
                                    
                                    # Create columns for main metrics
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        overall_accuracy = accuracy_data.get('overall_accuracy', 0)
                                        st.metric(
                                            "전체 정확도",
                                            f"{overall_accuracy:.1%}",
                                            help="여러 메트릭의 가중 평균"
                                        )
                                    
                                    with col2:
                                        context_relevance = accuracy_data.get('context_relevance', 0)
                                        st.metric(
                                            "컨텍스트 관련성",
                                            f"{context_relevance:.1%}",
                                            help="검색된 문서의 관련성"
                                        )
                                    
                                    with col3:
                                        answer_quality = accuracy_data.get('answer_quality', 0)
                                        st.metric(
                                            "답변 품질",
                                            f"{answer_quality:.1%}",
                                            help="생성된 답변의 품질"
                                        )
                                    
                                    with col4:
                                        confidence = accuracy_data.get('confidence', 0)
                                        st.metric(
                                            "신뢰도",
                                            f"{confidence:.1%}",
                                            help="시스템의 신뢰도"
                                        )
                                    
                                    # Additional metrics section
                                    st.markdown("### 📈 상세 메트릭")
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown("**응답 정보:**")
                                        st.write(f"- 응답 시간: {accuracy_data.get('response_time', 0):.2f}초")
                                        st.write(f"- 컨텍스트 수: {accuracy_data.get('context_count', 0)}개")
                                        st.write(f"- 평균 유사도: {accuracy_data.get('average_similarity', 0):.3f}")
                                        st.write(f"- 폴백 모드: {'사용됨' if accuracy_data.get('fallback_mode', False) else '사용 안됨'}")
                                    
                                    with col2:
                                        st.markdown("**시스템 상태:**")
                                        st.write(f"- 성공 여부: {'성공' if accuracy_data.get('success', False) else '실패'}")
                                        st.write(f"- 컨텍스트 파일: {len(accuracy_data.get('context_files', []))}개")
                                        if accuracy_data.get('similarity_scores'):
                                            st.write(f"- 유사도 점수: {[f'{s:.3f}' for s in accuracy_data['similarity_scores']]}")
                                    
                                    # Display generated response
                                    if accuracy_data.get('response'):
                                        st.markdown("### 💬 생성된 답변")
                                        st.info(f"측정 컬렉션: **{selected_collection}**")
                                        st.text_area("답변 내용", accuracy_data['response'], height=200, disabled=True)
                                    
                                    # Expected answer comparison
                                    if expected_answer and accuracy_data.get('similarity_to_expected'):
                                        st.markdown("### 🎯 예상 답변과의 유사도")
                                        similarity_to_expected = accuracy_data.get('similarity_to_expected', 0)
                                        st.metric(
                                            "유사도",
                                            f"{similarity_to_expected:.1%}",
                                            help="생성된 답변과 예상 답변 간의 유사도"
                                        )
                                    
                                else:
                                    st.error(f"❌ 정확도 측정 실패: {result.get('error', '알 수 없는 오류')}")
                            
                            except Exception as e:
                                st.error(f"❌ 정확도 측정 중 오류가 발생했습니다: {str(e)}")
                    else:
                        st.warning("⚠️ 질문을 입력해주세요.")
        
        with sub_tab2:
            st.markdown("### 🧪 정확도 테스트 스위트")
            st.write("여러 질문에 대한 종합적인 정확도 테스트를 실행합니다.")
            
            # Collection selection for test suite
            st.markdown("#### 📚 테스트 스위트 컬렉션 선택")
            
            # Get current collections for test suite
            collections_response = chat_controller.get_collections_response()
            if collections_response.get("success", False):
                collections = collections_response.get("collections", [])
                current_collection = collections_response.get("current_collection", "documents")
                
                # Remove duplicates and create collection options
                unique_collections = {}
                for collection in collections:
                    name = collection.get("name", "Unknown")
                    if name not in unique_collections:
                        unique_collections[name] = collection
                    else:
                        unique_collections[name]["document_count"] += collection.get("document_count", 0)
                
                # Display current collection
                st.info(f"현재 활성 컬렉션: **{current_collection}** ({unique_collections.get(current_collection, {}).get('document_count', 0)}개 문서)")
                
                # Collection selector for test suite
                collection_names = list(unique_collections.keys())
                test_selected_collection = st.selectbox(
                    "테스트 스위트에 사용할 컬렉션 선택:",
                    collection_names,
                    index=collection_names.index(current_collection) if current_collection in collection_names else 0,
                    help="테스트 스위트 실행에 사용할 컬렉션을 선택하세요.",
                    key="test_suite_collection_selector"
                )
                
                # Show collection info
                if test_selected_collection in unique_collections:
                    collection_info = unique_collections[test_selected_collection]
                    st.write(f"선택된 컬렉션: **{test_selected_collection}** ({collection_info.get('document_count', 0)}개 문서)")
                    
                    # Switch collection if different from current
                    if test_selected_collection != current_collection:
                        if st.button("🔄 테스트용 컬렉션 전환", key="switch_collection_for_test"):
                            try:
                                switch_response = chat_controller.switch_collection(test_selected_collection)
                                if switch_response.get("success", False):
                                    st.success(f"✅ 컬렉션이 '{test_selected_collection}'로 전환되었습니다.")
                                    st.rerun()
                                else:
                                    st.error(f"❌ 컬렉션 전환 실패: {switch_response.get('error', '알 수 없는 오류')}")
                            except Exception as e:
                                st.error(f"❌ 컬렉션 전환 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error(f"❌ 컬렉션 목록을 가져올 수 없습니다: {collections_response.get('error', '알 수 없는 오류')}")
                test_selected_collection = "documents"  # Fallback to default
            
            st.markdown("---")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**테스트 스위트 기능:**")
                st.write("• 샘플 질문 세트로 자동 테스트")
                st.write("• 전체 시스템 성능 평가")
                st.write("• 정확도 분포 분석")
                st.write("• 평균 응답 시간 측정")
            
            with col2:
                if st.button("샘플 테스트 실행", use_container_width=True, type="primary"):
                    with st.spinner(f"샘플 테스트를 실행하는 중... (컬렉션: {test_selected_collection})"):
                        try:
                            # Ensure the selected collection is active before running test
                            if test_selected_collection != current_collection:
                                switch_response = chat_controller.switch_collection(test_selected_collection)
                                if not switch_response.get("success", False):
                                    st.error(f"❌ 컬렉션 전환 실패: {switch_response.get('error', '알 수 없는 오류')}")
                                    return
                            
                            api_service = APIService()
                            result = api_service.run_accuracy_test_suite()
                            
                            if result.get("success"):
                                test_data = result.get("result", {})
                                aggregate = test_data.get("aggregate_metrics", {})
                                
                                st.success("✅ 테스트 스위트가 완료되었습니다!")
                                
                                # Display aggregate metrics
                                st.markdown("### 📊 전체 테스트 결과")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric(
                                        "성공률",
                                        f"{aggregate.get('success_rate', 0):.1%}",
                                        help="성공한 테스트의 비율"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "평균 정확도",
                                        f"{aggregate.get('average_accuracy', 0):.1%}",
                                        help="전체 테스트의 평균 정확도"
                                    )
                                
                                with col3:
                                    st.metric(
                                        "평균 응답 시간",
                                        f"{aggregate.get('average_response_time', 0):.2f}초",
                                        help="평균 응답 시간"
                                    )
                                
                                with col4:
                                    st.metric(
                                        "평균 신뢰도",
                                        f"{aggregate.get('average_confidence', 0):.1%}",
                                        help="평균 신뢰도"
                                    )
                                
                                # Accuracy distribution
                                st.markdown("### 📈 정확도 분포")
                                distribution = aggregate.get('accuracy_distribution', {})
                                
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric("높음 (80% 이상)", distribution.get('high', 0))
                                
                                with col2:
                                    st.metric("보통 (50-79%)", distribution.get('medium', 0))
                                
                                with col3:
                                    st.metric("낮음 (50% 미만)", distribution.get('low', 0))
                                
                                # Test details
                                st.markdown("### 📋 개별 테스트 결과")
                                st.info(f"테스트 실행 컬렉션: **{test_selected_collection}**")
                                test_results = test_data.get("test_suite_results", [])
                                
                                for i, test_result in enumerate(test_results, 1):
                                    with st.expander(f"테스트 {i}: {test_result.get('query', '')[:50]}..."):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.write(f"**정확도:** {test_result.get('overall_accuracy', 0):.1%}")
                                            st.write(f"**응답 시간:** {test_result.get('response_time', 0):.2f}초")
                                            st.write(f"**성공 여부:** {'성공' if test_result.get('success', False) else '실패'}")
                                        
                                        with col2:
                                            st.write(f"**컨텍스트 관련성:** {test_result.get('context_relevance', 0):.1%}")
                                            st.write(f"**답변 품질:** {test_result.get('answer_quality', 0):.1%}")
                                            st.write(f"**신뢰도:** {test_result.get('confidence', 0):.1%}")
                                        
                                        if test_result.get('response'):
                                            st.text_area("생성된 답변", test_result['response'], height=100, disabled=True)
                            
                            else:
                                st.error(f"❌ 테스트 스위트 실행 실패: {result.get('error', '알 수 없는 오류')}")
                        
                        except Exception as e:
                            st.error(f"❌ 테스트 스위트 실행 중 오류가 발생했습니다: {str(e)}")
        
        with sub_tab3:
            st.markdown("### 📈 시스템 상태 모니터링")
            st.write("RAG 시스템의 전반적인 상태와 성능을 모니터링합니다.")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**모니터링 항목:**")
                st.write("• 문서 데이터베이스 상태")
                st.write("• 시스템 성능 지표")
                st.write("• 정확도 및 신뢰도 통계")
                st.write("• 서비스 연결 상태")
            
            with col2:
                if st.button("시스템 상태 확인", use_container_width=True, type="primary"):
                    with st.spinner("시스템 상태를 확인하는 중..."):
                        try:
                            api_service = APIService()
                            result = api_service.get_system_health()
                            
                            if result.get("success"):
                                health_data = result.get("result", {})
                                
                                st.success("✅ 시스템 상태 확인이 완료되었습니다!")
                                
                                # Document count
                                st.markdown("### 📚 문서 데이터베이스")
                                doc_count = health_data.get("document_count", 0)
                                st.metric("총 문서 수", doc_count)
                                
                                # Collections info
                                collections = health_data.get("collections", [])
                                if collections:
                                    st.markdown("#### 컬렉션 정보")
                                    for collection in collections:
                                        st.write(f"- **{collection.get('name', 'Unknown')}**: {collection.get('document_count', 0)}개 문서")
                                
                                # Test query result
                                test_result = health_data.get("test_query_result", {})
                                if test_result:
                                    st.markdown("### 🧪 테스트 쿼리 결과")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.metric(
                                            "응답 시간",
                                            f"{test_result.get('response_time', 0):.2f}초"
                                        )
                                    
                                    with col2:
                                        st.metric(
                                            "정확도",
                                            f"{test_result.get('overall_accuracy', 0):.1%}"
                                        )
                                    
                                    with col3:
                                        st.metric(
                                            "신뢰도",
                                            f"{test_result.get('confidence', 0):.1%}"
                                        )
                                    
                                    if test_result.get('response'):
                                        st.text_area("테스트 응답", test_result['response'], height=100, disabled=True)
                            
                            else:
                                st.error(f"❌ 시스템 상태 확인 실패: {result.get('error', '알 수 없는 오류')}")
                        
                        except Exception as e:
                            st.error(f"❌ 시스템 상태 확인 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
