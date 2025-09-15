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

# Page configuration
st.set_page_config(
    page_title="접근성 데모 - HAI Portal",
    page_icon="♿",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Accessibility demo page"""
    st.title("♿ 접근성 데모 페이지")
    st.markdown("---")
    
    # Inject accessibility scripts
    ChatComponents._inject_accessibility_scripts()
    
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
    
    # Back to main page
    st.markdown("---")
    if st.button("🏠 메인 페이지로 돌아가기", use_container_width=True):
        st.switch_page("main.py")

if __name__ == "__main__":
    main()
