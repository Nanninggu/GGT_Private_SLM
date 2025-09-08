#!/bin/bash
# 프론트엔드 Streamlit 앱 시작 스크립트

echo "🎨 Exaone 챗봇 프론트엔드를 시작합니다..."

# 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 가상환경이 활성화되어 있습니다: $VIRTUAL_ENV"
else
    echo "⚠️ 가상환경을 먼저 활성화해주세요: source .venv/bin/activate"
    exit 1
fi

# 의존성 설치
echo "📦 의존성을 설치합니다..."
pip install -r frontend/requirements.txt

# Streamlit 앱 시작
echo "🌟 Streamlit 앱을 시작합니다..."
echo "📍 앱 주소: http://localhost:8501"
echo "💡 백엔드 서버(http://localhost:8000)가 실행 중인지 확인해주세요!"
echo ""
cd frontend/streamlit
streamlit run main.py
