#!/bin/bash
# 서비스 완전 재시작 스크립트

echo "🔄 서비스를 완전히 재시작합니다..."

# 1. 모든 프로세스 종료
echo "📛 기존 프로세스 종료 중..."
sudo pkill -f python
sudo pkill -f main.py
sudo pkill -f node

# 2. 잠시 대기
echo "⏳ 잠시 대기 중..."
sleep 3

# 3. 캐시 삭제
echo "🗑️ 캐시 삭제 중..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 4. 환경변수 설정
echo "🔧 환경변수 설정 중..."
export API_BASE_URL=http://localhost:9502
export SERVER_PORT=9502

# 5. 백엔드 시작
echo "🚀 백엔드 시작 중..."
cd backend
python main.py &
BACKEND_PID=$!

# 6. 잠시 대기
sleep 5

# 7. 프론트엔드 시작
echo "🌐 프론트엔드 시작 중..."
cd vue-frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ 서비스가 시작되었습니다!"
echo "📍 프론트엔드: http://localhost:5173"
echo "📍 백엔드: http://localhost:9502"
echo ""
echo "종료하려면 Ctrl+C를 누르세요"

# 프로세스 모니터링
wait
