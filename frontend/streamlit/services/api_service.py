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
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str = "text/plain", collection_name: str = "documents") -> Dict[str, Any]:
        """Upload file to backend for vectorization"""
        try:
            files = {
                'file': (filename, io.BytesIO(file_content), content_type)
            }
            data = {
                'collection_name': collection_name
            }
            
            response = requests.post(
                f"{self.base_url}/api/upload",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def upload_file_langchain(self, file_content: bytes, filename: str, content_type: str = "text/plain", collection_name: str = "documents") -> Dict[str, Any]:
        """Upload file to LangChain backend for vectorization"""
        try:
            files = {
                'file': (filename, io.BytesIO(file_content), content_type)
            }
            data = {
                'collection_name': collection_name
            }
            
            response = requests.post(
                f"{self.base_url}/api/langchain/upload",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def upload_multiple_files(self, file_list: List[Dict[str, Any]], collection_name: str = "documents") -> Dict[str, Any]:
        """Upload multiple files to backend for vectorization"""
        try:
            files = []
            for file_info in file_list:
                files.append(('files', (
                    file_info['filename'], 
                    io.BytesIO(file_info['content']), 
                    file_info['content_type']
                )))
            
            data = {
                'collection_name': collection_name
            }
            
            response = requests.post(
                f"{self.base_url}/api/upload/multiple",
                files=files,
                data=data,
                timeout=self.timeout * 2  # Longer timeout for multiple files
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def upload_multiple_files_langchain(self, file_list: List[Dict[str, Any]], collection_name: str = "documents") -> Dict[str, Any]:
        """Upload multiple files to LangChain backend for vectorization"""
        try:
            files = []
            for file_info in file_list:
                files.append(('files', (
                    file_info['filename'], 
                    io.BytesIO(file_info['content']), 
                    file_info['content_type']
                )))
            
            data = {
                'collection_name': collection_name
            }
            
            response = requests.post(
                f"{self.base_url}/api/langchain/upload/multiple",
                files=files,
                data=data,
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
    
    # Collection Management Methods
    def get_collections(self) -> Dict[str, Any]:
        """Get list of available vector database collections"""
        try:
            response = requests.get(
                f"{self.base_url}/api/collections",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_current_collection(self) -> Dict[str, Any]:
        """Get the currently active collection"""
        try:
            response = requests.get(
                f"{self.base_url}/api/collections/active",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def switch_collection(self, collection_name: str) -> Dict[str, Any]:
        """Switch the active collection for RAG queries"""
        try:
            payload = {"collection_name": collection_name}
            response = requests.post(
                f"{self.base_url}/api/collections/switch",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific collection"""
        try:
            response = requests.get(
                f"{self.base_url}/api/collections/info/{collection_name}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def create_collection(self, collection_name: str, description: str = "") -> Dict[str, Any]:
        """Create a new collection"""
        try:
            payload = {
                "collection_name": collection_name,
                "description": description
            }
            response = requests.post(
                f"{self.base_url}/api/collections/create",
                json=payload,
                timeout=self.timeout
            )
            
            # Handle HTTP 400 (Bad Request) as a normal response, not an exception
            if response.status_code == 400:
                try:
                    error_detail = response.json()
                    return {"success": False, "error": error_detail.get('detail', 'Bad Request')}
                except:
                    return {"success": False, "error": "Bad Request"}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Get detailed error information for other HTTP errors
            try:
                error_detail = response.json()
                return {"success": False, "error": f"HTTP {response.status_code}: {error_detail.get('detail', str(e))}"}
            except:
                return {"success": False, "error": f"HTTP {response.status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def switch_collection(self, collection_name: str) -> Dict[str, Any]:
        """Switch active collection"""
        try:
            payload = {
                "collection_name": collection_name
            }
            response = requests.post(
                f"{self.base_url}/api/collections/switch",
                json=payload,
                timeout=self.timeout
            )
            
            # Handle HTTP 400 (Bad Request) as a normal response, not an exception
            if response.status_code == 400:
                try:
                    error_detail = response.json()
                    return {"success": False, "error": error_detail.get('detail', 'Bad Request')}
                except:
                    return {"success": False, "error": "Bad Request"}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Get detailed error information for other HTTP errors
            try:
                error_detail = response.json()
                return {"success": False, "error": f"HTTP {response.status_code}: {error_detail.get('detail', str(e))}"}
            except:
                return {"success": False, "error": f"HTTP {response.status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection and all its documents"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/collections/{collection_name}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def rename_collection(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a collection"""
        try:
            payload = {
                "old_name": old_name,
                "new_name": new_name
            }
            response = requests.put(
                f"{self.base_url}/api/collections/rename",
                json=payload,
                timeout=self.timeout
            )
            
            # Handle HTTP 400 (Bad Request) as a normal response, not an exception
            if response.status_code == 400:
                try:
                    error_detail = response.json()
                    return {"success": False, "error": error_detail.get('detail', 'Bad Request')}
                except:
                    return {"success": False, "error": "Bad Request"}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Get detailed error information for other HTTP errors
            try:
                error_detail = response.json()
                return {"success": False, "error": f"HTTP {response.status_code}: {error_detail.get('detail', str(e))}"}
            except:
                return {"success": False, "error": f"HTTP {response.status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}