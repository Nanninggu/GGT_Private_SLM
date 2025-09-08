"""
API service for communicating with backend
"""
import requests
import streamlit as st
from typing import Dict, Any, List, Optional, Generator
import io
import json

class APIService:
    """Service for backend API communication"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.timeout = 30

    def create_session(self) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/session",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def send_message(self, message: str, session_id: Optional[str] = None, use_rag: bool = True) -> Dict[str, Any]:
        """Send a message to the chatbot"""
        try:
            payload = {
                "message": message,
                "use_rag": use_rag
            }
            if session_id:
                payload["session_id"] = session_id

            response = requests.post(
                f"{self.base_url}/api/chat/message",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_chat_history(self, session_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get chat history for a session"""
        try:
            params = {}
            if limit:
                params["limit"] = limit

            response = requests.get(
                f"{self.base_url}/api/chat/history/{session_id}",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_sessions(self) -> Dict[str, Any]:
        """Get all session IDs"""
        try:
            response = requests.get(
                f"{self.base_url}/api/chat/sessions",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear a chat session"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/chat/session/{session_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def health_check(self) -> bool:
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def send_message_langchain(self, message: str, session_id: Optional[str] = None, use_rag: bool = True) -> Dict[str, Any]:
        """Send a message using LangChain RAG"""
        try:
            payload = {
                "message": message,
                "use_rag": use_rag
            }
            if session_id:
                payload["session_id"] = session_id

            response = requests.post(
                f"{self.base_url}/api/langchain/chat/message",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def add_document_langchain(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add document to LangChain knowledge base"""
        try:
            payload = {
                "content": content,
                "metadata": metadata or {}
            }
            
            response = requests.post(
                f"{self.base_url}/api/langchain/documents",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def clear_langchain_memory(self, session_id: str) -> Dict[str, Any]:
        """Clear LangChain conversation memory"""
        try:
            payload = {"session_id": session_id}
            
            response = requests.post(
                f"{self.base_url}/api/langchain/memory/clear",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_langchain_memory_state(self) -> Dict[str, Any]:
        """Get LangChain memory state"""
        try:
            response = requests.get(
                f"{self.base_url}/api/langchain/memory/state",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str = "text/plain") -> Dict[str, Any]:
        """Upload file to backend for vectorization"""
        try:
            files = {
                'file': (filename, io.BytesIO(file_content), content_type)
            }
            
            response = requests.post(
                f"{self.base_url}/api/upload",
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def upload_file_langchain(self, file_content: bytes, filename: str, content_type: str = "text/plain") -> Dict[str, Any]:
        """Upload file to LangChain backend for vectorization"""
        try:
            files = {
                'file': (filename, io.BytesIO(file_content), content_type)
            }
            
            response = requests.post(
                f"{self.base_url}/api/langchain/upload",
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def upload_multiple_files(self, file_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload multiple files to backend for vectorization"""
        try:
            files = []
            for file_info in file_list:
                files.append(('files', (
                    file_info['filename'], 
                    io.BytesIO(file_info['content']), 
                    file_info['content_type']
                )))
            
            response = requests.post(
                f"{self.base_url}/api/upload/multiple",
                files=files,
                timeout=self.timeout * 2  # Longer timeout for multiple files
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def upload_multiple_files_langchain(self, file_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload multiple files to LangChain backend for vectorization"""
        try:
            files = []
            for file_info in file_list:
                files.append(('files', (
                    file_info['filename'], 
                    io.BytesIO(file_info['content']), 
                    file_info['content_type']
                )))
            
            response = requests.post(
                f"{self.base_url}/api/langchain/upload/multiple",
                files=files,
                timeout=self.timeout * 2  # Longer timeout for multiple files
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def send_message_stream(self, message: str, session_id: Optional[str] = None, use_rag: bool = True) -> Generator[Dict[str, Any], None, None]:
        """Send a message to the chatbot with streaming response"""
        try:
            url = f"{self.base_url}/api/chat/stream"
            if use_rag:
                url = f"{self.base_url}/api/chat/stream/langchain"
            
            payload = {
                "message": message,
                "session_id": session_id
            }
            
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            yield data
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RequestException as e:
            yield {"error": str(e), "finished": True}
    
    def send_message_stream_basic(self, message: str, session_id: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """Send a message to the chatbot with basic streaming response"""
        try:
            url = f"{self.base_url}/api/chat/stream"
            
            payload = {
                "message": message,
                "session_id": session_id
            }
            
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            yield data
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RequestException as e:
            yield {"error": str(e), "finished": True}
