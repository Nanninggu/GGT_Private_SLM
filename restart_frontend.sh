#!/bin/bash

# Script to restart frontend with cache clearing

echo "🔄 Streamlit 프론트엔드 재시작 중..."

# Kill any running Streamlit processes
echo "🛑 기존 Streamlit 프로세스 종료..."
pkill -f "streamlit run"
sleep 2

# Clear Streamlit cache
echo "🧹 Streamlit 캐시 삭제..."
rm -rf frontend/streamlit/.streamlit/cache
rm -rf ~/.streamlit/cache

# Clear Python cache files
echo "🧹 Python 캐시 삭제..."
find frontend/streamlit -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find frontend/streamlit -type f -name "*.pyc" -delete

# Start Streamlit
echo "🚀 Streamlit 시작..."
cd frontend/streamlit
source ../../.venv/bin/activate 2>/dev/null || python3 -m venv ../../.venv && source ../../.venv/bin/activate
streamlit run app.py --server.port=8501 --server.address=0.0.0.0

echo "✅ Streamlit 재시작 완료!"
