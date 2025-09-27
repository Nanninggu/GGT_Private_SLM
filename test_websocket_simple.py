#!/usr/bin/env python3
"""
Simple WebSocket connection test
"""
import asyncio
import websockets
import json
import sys

async def test_websocket_connection():
    """Test basic WebSocket connection"""
    uri = "ws://localhost:8002/ws/chat/test_session"
    
    try:
        print("🔌 WebSocket 연결 테스트...")
        print(f"연결 URL: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공!")
            
            # Send a simple test message
            test_message = {
                "message": "안녕하세요! 연결 테스트입니다.",
                "rag_mode": "LangChain RAG",
                "model_type": "fast"
            }
            
            print("📤 테스트 메시지 전송...")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"📥 응답 수신: {data}")
                print("✅ WebSocket 테스트 성공!")
            except asyncio.TimeoutError:
                print("⏰ 응답 시간 초과 (10초)")
            except Exception as e:
                print(f"❌ 응답 처리 오류: {e}")
                
    except websockets.exceptions.ConnectionRefused:
        print("❌ WebSocket 연결 실패: 백엔드 서버가 실행 중인지 확인하세요.")
        print("백엔드 시작: cd backend && python main.py")
    except Exception as e:
        print(f"❌ 연결 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
