"""
WebSocket service for real-time chat communication
"""
import asyncio
import json
import streamlit as st
from typing import Dict, Any, Callable, Optional, Generator
import websockets
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketService:
    """Service for WebSocket communication with backend"""
    
    def __init__(self, base_url: str = "ws://localhost:9502"):
        self.base_url = base_url
        self.websocket = None
        self.session_id = None
        self.is_connected = False
        self.message_handlers = {}
        self.connection_retry_count = 0
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    async def connect(self, session_id: str) -> bool:
        """Connect to WebSocket server with retry logic"""
        self.session_id = session_id
        ws_url = f"{self.base_url}/ws/chat/{session_id}"
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Connecting to WebSocket (attempt {attempt + 1}/{self.max_retries}): {ws_url}")
                self.websocket = await websockets.connect(ws_url, ping_interval=20, ping_timeout=10)
                self.is_connected = True
                self.connection_retry_count = 0
                
                logger.info(f"WebSocket connected successfully for session {session_id}")
                return True
                
            except websockets.exceptions.ConnectionRefused:
                logger.warning(f"WebSocket connection refused (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("WebSocket connection failed after all retries")
                    self.is_connected = False
                    return False
                    
            except Exception as e:
                logger.error(f"WebSocket connection failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.is_connected = False
                    return False
        
        return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        try:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            self.is_connected = False
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")
    
    async def send_message(self, message: str, rag_mode: str = "LangChain RAG", 
                          model_type: str = "fast", collection_names: Optional[list] = None) -> bool:
        """Send message to WebSocket server"""
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected")
            return False
        
        try:
            message_data = {
                "message": message,
                "rag_mode": rag_mode,
                "model_type": model_type,
                "collection_names": collection_names,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(message_data))
            logger.debug(f"Message sent: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.is_connected = False
            return False
    
    async def listen_for_messages(self, on_message: Optional[Callable[[Dict[str, Any]], None]] = None) -> Generator[Dict[str, Any], None, None]:
        """Listen for messages from WebSocket server"""
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected")
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    yield data
                    if on_message:
                        await on_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    continue
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
            yield {"type": "error", "message": "연결이 종료되었습니다."}
        except Exception as e:
            logger.error(f"WebSocket listening error: {e}")
            self.is_connected = False
            yield {"type": "error", "message": f"연결 오류: {str(e)}"}
    
    async def send_message_stream(self, message: str, rag_mode: str = "LangChain RAG", 
                                model_type: str = "fast", collection_names: Optional[list] = None) -> Generator[Dict[str, Any], None, None]:
        """Send message and get streaming response"""
        logger.info(f"Starting send_message_stream: {message[:50]}...")
        
        if not await self.send_message(message, rag_mode, model_type, collection_names):
            logger.error("Failed to send message")
            yield {"type": "error", "message": "메시지 전송에 실패했습니다."}
            return
        
        logger.info("Message sent successfully, listening for response...")
        
        # Listen for streaming response (without callback)
        try:
            async for data in self.listen_for_messages():
                logger.debug(f"Received data: {data.get('type', 'unknown')}")
                yield data
        except Exception as e:
            logger.error(f"Error in send_message_stream: {e}")
            yield {"type": "error", "message": f"스트리밍 중 오류: {str(e)}"}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            "connected": self.is_connected,
            "session_id": self.session_id,
            "websocket_url": f"{self.base_url}/ws/chat/{self.session_id}" if self.session_id else None
        }
    
    async def health_check(self) -> bool:
        """Check if WebSocket connection is healthy"""
        if not self.is_connected or not self.websocket:
            return False
        
        try:
            # Send ping to check connection
            await self.websocket.ping()
            return True
        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            self.is_connected = False
            return False

class WebSocketManager:
    """Singleton manager for WebSocket connections"""
    
    _instance = None
    _websocket_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebSocketManager, cls).__new__(cls)
        return cls._instance
    
    def get_service(self, session_id: str = None) -> WebSocketService:
        """Get or create WebSocket service"""
        if self._websocket_service is None or (session_id and self._websocket_service.session_id != session_id):
            self._websocket_service = WebSocketService()
        return self._websocket_service
    
    async def cleanup(self):
        """Cleanup WebSocket connections"""
        if self._websocket_service:
            await self._websocket_service.disconnect()
            self._websocket_service = None

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
