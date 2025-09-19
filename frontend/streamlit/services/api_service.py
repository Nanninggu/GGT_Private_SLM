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

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 60  # 기본 타임아웃을 60초로 증가
        self.upload_timeout = 600  # 파일 업로드 전용 타임아웃을 10분으로 증가

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

    def send_message(self, message: str, session_id: Optional[str] = None, use_rag: bool = True, rag_mode: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to the chatbot"""
        try:
            payload = {
                "message": message,
                "use_rag": use_rag
            }
            if session_id:
                payload["session_id"] = session_id
            if rag_mode:
                payload["rag_mode"] = rag_mode

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

    def check_session_exists(self, session_id: str) -> Dict[str, Any]:
        """Check if a session exists without loading all sessions"""
        try:
            response = requests.get(
                f"{self.base_url}/api/chat/session/{session_id}/exists",
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

    def clear_all_sessions(self) -> Dict[str, Any]:
        """Clear all sessions except default"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/chat/sessions/all",
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
    
    def send_message_langchain(self, message: str, session_id: Optional[str] = None, use_rag: bool = True, rag_mode: Optional[str] = None) -> Dict[str, Any]:
        """Send a message using LangChain RAG"""
        try:
            payload = {
                "message": message,
                "use_rag": use_rag
            }
            if session_id:
                payload["session_id"] = session_id
            if rag_mode:
                payload["rag_mode"] = rag_mode

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
                timeout=self.upload_timeout
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
                timeout=self.upload_timeout
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
                timeout=self.upload_timeout * 3  # Longer timeout for multiple files (30분)
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
                timeout=self.upload_timeout * 3  # Longer timeout for multiple files (30분)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def send_message_stream(self, message: str, session_id: Optional[str] = None, use_rag: bool = True, rag_mode: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """Send a message to the chatbot with streaming response"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                url = f"{self.base_url}/api/chat/stream"
                if use_rag:
                    url = f"{self.base_url}/api/chat/stream/langchain"
                
                payload = {
                    "message": message,
                    "session_id": session_id
                }
                if rag_mode:
                    payload["rag_mode"] = rag_mode
                
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
                
                # If we get here, streaming completed successfully
                break
                            
            except requests.exceptions.ConnectionError as e:
                retry_count += 1
                if retry_count < max_retries:
                    yield {"error": f"연결 오류 (재시도 {retry_count}/{max_retries}): {str(e)}", "retrying": True, "finished": False}
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry
                else:
                    yield {"error": f"연결 실패: {str(e)}", "finished": True}
            except requests.exceptions.Timeout as e:
                retry_count += 1
                if retry_count < max_retries:
                    yield {"error": f"시간 초과 (재시도 {retry_count}/{max_retries}): {str(e)}", "retrying": True, "finished": False}
                    import time
                    time.sleep(1)
                else:
                    yield {"error": f"시간 초과: {str(e)}", "finished": True}
            except requests.exceptions.RequestException as e:
                yield {"error": f"요청 오류: {str(e)}", "finished": True}
                break
    
    def send_message_stream_basic(self, message: str, session_id: Optional[str] = None, rag_mode: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """Send a message to the chatbot with basic streaming response"""
        try:
            url = f"{self.base_url}/api/chat/stream"
            
            payload = {
                "message": message,
                "session_id": session_id
            }
            if rag_mode:
                payload["rag_mode"] = rag_mode
            
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
    
    # Markdown Export Methods
    def export_chat_markdown(self, session_id: str, session_name: str = "채팅 기록", include_metadata: bool = True) -> Dict[str, Any]:
        """Export chat session to markdown format"""
        try:
            payload = {
                "session_id": session_id,
                "session_name": session_name,
                "include_metadata": include_metadata
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat/export/markdown",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def export_single_message_markdown(self, message: Dict[str, Any], include_metadata: bool = True) -> Dict[str, Any]:
        """Export a single message to markdown format"""
        try:
            payload = {
                "message": message,
                "include_metadata": include_metadata
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat/export/markdown/single",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_markdown_export_stats(self) -> Dict[str, Any]:
        """Get statistics about exported markdown files"""
        try:
            response = requests.get(
                f"{self.base_url}/api/chat/export/markdown/stats",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def download_markdown_file(self, filename: str) -> Dict[str, Any]:
        """Download a specific markdown file"""
        try:
            response = requests.get(
                f"{self.base_url}/api/chat/export/markdown/download/{filename}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    # Authentication Methods
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user"""
        try:
            payload = {
                "username": username,
                "password": password
            }
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": str(e)}
    
    def register(self, username: str, email: str, password: str, confirm_password: str) -> Dict[str, Any]:
        """Register user"""
        try:
            payload = {
                "username": username,
                "email": email,
                "password": password,
                "confirm_password": confirm_password
            }
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": str(e)}
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            payload = {
                "refresh_token": refresh_token
            }
            response = requests.post(
                f"{self.base_url}/api/auth/refresh",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": str(e)}
    
    def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get current user information"""
        try:
            headers = {
                "Authorization": f"Bearer {token}"
            }
            response = requests.get(
                f"{self.base_url}/api/auth/me",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def logout(self, token: str) -> Dict[str, Any]:
        """Logout user"""
        try:
            headers = {
                "Authorization": f"Bearer {token}"
            }
            response = requests.post(
                f"{self.base_url}/api/auth/logout",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify if token is valid"""
        try:
            payload = {"token": token}
            response = requests.post(
                f"{self.base_url}/api/auth/verify",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "valid": False, "error": str(e)}
    
    # Accuracy Measurement Methods
    def measure_query_accuracy(self, query: str, expected_answer: Optional[str] = None) -> Dict[str, Any]:
        """Measure accuracy for a single query"""
        try:
            payload = {
                "query": query,
                "expected_answer": expected_answer
            }
            response = requests.post(
                f"{self.base_url}/api/accuracy/measure",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def run_accuracy_test_suite(self, test_queries: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Run a comprehensive accuracy test suite"""
        try:
            if test_queries is None:
                # Get sample test queries
                sample_response = self.get_sample_test_queries()
                if sample_response.get("success"):
                    test_queries = sample_response.get("sample_queries", [])
                else:
                    return {"success": False, "error": "Failed to get sample test queries"}
            
            payload = {"test_queries": test_queries}
            response = requests.post(
                f"{self.base_url}/api/accuracy/test-suite",
                json=payload,
                timeout=self.timeout * 2  # Longer timeout for test suite
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            response = requests.get(
                f"{self.base_url}/api/accuracy/system-health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def get_sample_test_queries(self) -> Dict[str, Any]:
        """Get sample test queries for accuracy testing"""
        try:
            response = requests.get(
                f"{self.base_url}/api/accuracy/sample-queries",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}