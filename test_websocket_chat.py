#!/usr/bin/env python3
"""
Test script for WebSocket chat functionality
"""
import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_websocket_chat():
    """Test WebSocket chat connection and messaging"""
    uri = "ws://localhost:8002/ws/chat/test_session"
    
    try:
        print("🔌 WebSocket 채팅 테스트 시작...")
        print(f"연결 URL: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공!")
            
            # Test message
            test_message = {
                "message": "안녕하세요! 웹소켓 채팅 테스트입니다.",
                "rag_mode": "LangChain RAG",
                "model_type": "fast",
                "collection_names": None,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📤 메시지 전송: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Listen for responses
            print("📥 응답 수신 중...")
            response_count = 0
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response_count += 1
                    
                    if data["type"] == "status":
                        print(f"📊 상태: {data['message']}")
                    
                    elif data["type"] == "context":
                        sources = data.get("sources", [])
                        print(f"📚 참고 문서: {len(sources)}개")
                        for i, source in enumerate(sources, 1):
                            print(f"  {i}. {source}")
                    
                    elif data["type"] == "chunk":
                        if not data.get("finished", False):
                            print(f"💬 응답 청크: {data['content']}", end="", flush=True)
                        else:
                            print(f"\n✅ 응답 완료!")
                            model_info = data.get("model_info", {})
                            if model_info:
                                print(f"🤖 모델: {model_info.get('model_name', 'Unknown')}")
                            break
                    
                    elif data["type"] == "error":
                        print(f"❌ 오류: {data['message']}")
                        break
                    
                    # Limit response count to prevent infinite loop
                    if response_count > 100:
                        print("\n⚠️ 응답 수신 제한에 도달했습니다.")
                        break
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    continue
                except Exception as e:
                    print(f"❌ 메시지 처리 오류: {e}")
                    continue
            
            print("✅ WebSocket 채팅 테스트 완료!")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ WebSocket 연결 실패: 서버가 실행 중인지 확인하세요.")
        print("백엔드 서버를 시작하려면: cd backend && python main.py")
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")

async def test_websocket_status():
    """Test WebSocket status endpoint"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test status endpoint
            async with session.get("http://localhost:8002/api/websocket/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print("📊 WebSocket 상태:")
                    print(f"  활성 연결 수: {data.get('active_connections', 0)}")
                    print(f"  연결된 세션: {data.get('connections', [])}")
                else:
                    print(f"❌ 상태 확인 실패: HTTP {response.status}")
    except Exception as e:
        print(f"❌ 상태 확인 오류: {e}")

async def main():
    """Main test function"""
    print("🚀 WebSocket 채팅 시스템 테스트")
    print("=" * 50)
    
    # Test status first
    print("\n1. WebSocket 상태 확인...")
    await test_websocket_status()
    
    # Test chat functionality
    print("\n2. WebSocket 채팅 테스트...")
    await test_websocket_chat()
    
    print("\n" + "=" * 50)
    print("테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
