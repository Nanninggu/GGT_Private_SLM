#!/bin/bash
# 백엔드 서버 시작 스크립트 (Spring Boot properties 변환 적용)

echo "🚀 SLM Pattern 백엔드 서버를 시작합니다..."

# 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 가상환경이 활성화되어 있습니다: $VIRTUAL_ENV"
else
    echo "⚠️ 가상환경을 먼저 활성화해주세요: source .venv/bin/activate"
    exit 1
fi

# 의존성 설치
echo "📦 의존성을 설치합니다..."
pip install -r backend/requirements.txt

# 데이터 디렉토리 생성
mkdir -p data

# 환경 변수 파일 확인
if [ ! -f "backend/.env" ]; then
    echo "⚠️  .env 파일이 없습니다. 예제에서 생성합니다..."
    if [ -f "backend/env.example" ]; then
        cp backend/env.example backend/.env
        echo "✅ .env 파일을 생성했습니다. 실제 값으로 업데이트해주세요."
    else
        echo "❌ env.example 파일을 찾을 수 없습니다. .env 파일을 수동으로 생성해주세요."
        exit 1
    fi
fi

# 설정 테스트
echo "🧪 설정을 테스트합니다..."
cd backend
python test_configuration.py

if [ $? -eq 0 ]; then
    echo "✅ 설정 테스트 통과!"
else
    echo "❌ 설정 테스트 실패. 설정을 확인해주세요."
    echo "💡 PostgreSQL과 Ollama가 실행 중인지 확인해주세요."
    exit 1
fi

# 백엔드 서버 시작
echo "🌟 FastAPI 서버를 시작합니다..."
echo "📍 서버 주소: http://localhost:8080"
echo "📖 API 문서: http://localhost:8080/docs"
echo "🔍 헬스체크: http://localhost:8080/health"
echo "ℹ️  앱 정보: http://localhost:8080/info"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요"
echo "=" * 50

python main.py
