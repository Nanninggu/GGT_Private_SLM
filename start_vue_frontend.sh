#!/bin/bash

# Vue Frontend 시작 스크립트

cd "$(dirname "$0")/vue-frontend"

echo "🚀 Vue Frontend 서버를 시작합니다..."
echo "📍 포트: 5173"
echo "🌐 URL: http://localhost:5173"
echo ""

npm run dev

