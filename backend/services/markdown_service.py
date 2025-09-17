"""
Markdown export service for chat messages
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MarkdownService:
    """Service for generating markdown exports of chat conversations"""
    
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def generate_chat_markdown(
        self, 
        messages: List[Dict[str, Any]], 
        session_id: str = "default",
        session_name: str = "채팅 기록",
        include_metadata: bool = True
    ) -> str:
        """
        Generate markdown content from chat messages
        
        Args:
            messages: List of chat messages
            session_id: Session identifier
            session_name: Display name for the session
            include_metadata: Whether to include metadata like timestamps and similarity scores
            
        Returns:
            Formatted markdown string
        """
        try:
            # Create markdown header
            markdown_content = self._create_header(session_name, session_id, len(messages))
            
            # Add messages
            for i, message in enumerate(messages, 1):
                markdown_content += self._format_message(message, i, include_metadata)
            
            # Add footer
            markdown_content += self._create_footer()
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"Error generating markdown: {e}")
            return f"# 오류\n\n마크다운 생성 중 오류가 발생했습니다: {str(e)}"
    
    def generate_single_message_markdown(
        self, 
        message: Dict[str, Any], 
        include_metadata: bool = True
    ) -> str:
        """
        Generate markdown for a single message
        
        Args:
            message: Single chat message
            include_metadata: Whether to include metadata
            
        Returns:
            Formatted markdown string
        """
        try:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            # Create header
            markdown_content = f"# 개별 메시지\n\n"
            markdown_content += f"**생성 시간:** {self._format_timestamp(timestamp)}\n\n"
            
            # Add message content
            if role == "user":
                markdown_content += f"## 👤 사용자\n\n{content}\n\n"
            else:
                markdown_content += f"## 🤖 AI 어시스턴트\n\n{content}\n\n"
            
            # Add metadata if requested
            if include_metadata:
                metadata = message.get("metadata", {})
                if metadata:
                    markdown_content += self._format_metadata(metadata)
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"Error generating single message markdown: {e}")
            return f"# 오류\n\n마크다운 생성 중 오류가 발생했습니다: {str(e)}"
    
    def save_markdown_to_file(
        self, 
        markdown_content: str, 
        filename: str
    ) -> str:
        """
        Save markdown content to file
        
        Args:
            markdown_content: Markdown content to save
            filename: Name of the file (without extension)
            
        Returns:
            Path to the saved file
        """
        try:
            # Ensure filename has .md extension
            if not filename.endswith('.md'):
                filename += '.md'
            
            filepath = os.path.join(self.export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Markdown saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving markdown file: {e}")
            raise
    
    def _create_header(self, session_name: str, session_id: str, message_count: int) -> str:
        """Create markdown header"""
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        
        header = f"""# {session_name}

**세션 ID:** `{session_id}`  
**생성 시간:** {current_time}  
**총 메시지 수:** {message_count}개

---

"""
        return header
    
    def _format_message(self, message: Dict[str, Any], message_number: int, include_metadata: bool) -> str:
        """Format a single message for markdown"""
        role = message.get("role", "unknown")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        metadata = message.get("metadata", {})
        context = message.get("context", [])
        
        # Message header
        if role == "user":
            formatted_message = f"## {message_number}. 👤 사용자\n\n"
        else:
            formatted_message = f"## {message_number}. 🤖 AI 어시스턴트\n\n"
        
        # Add timestamp if available
        if timestamp:
            formatted_message += f"**시간:** {self._format_timestamp(timestamp)}\n\n"
        
        # Add content
        formatted_message += f"{content}\n\n"
        
        # Add context if available
        if context:
            formatted_message += "**참조 문서:**\n"
            for i, ctx in enumerate(context, 1):
                source = ctx.get("source", f"문서 {i}")
                formatted_message += f"- {source}\n"
            formatted_message += "\n"
        
        # Add metadata if requested
        if include_metadata and metadata:
            formatted_message += self._format_metadata(metadata)
        
        formatted_message += "---\n\n"
        return formatted_message
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for markdown"""
        metadata_section = "**메타데이터:**\n\n"
        
        # Similarity score
        if "similarity" in metadata:
            similarity = metadata["similarity"]
            similarity_percent = round(similarity * 100, 1)
            metadata_section += f"- **신뢰도:** {similarity_percent}%\n"
        
        # Context count
        if "context_count" in metadata:
            context_count = metadata["context_count"]
            metadata_section += f"- **참조 문서 수:** {context_count}개\n"
        
        # Context files
        if "context_files" in metadata:
            context_files = metadata["context_files"]
            if context_files:
                metadata_section += f"- **참조 파일:** {', '.join(context_files)}\n"
        
        # Model information
        if "model_name" in metadata:
            model_name = metadata["model_name"]
            metadata_section += f"- **모델:** {model_name}\n"
        
        # Response time
        if "response_time" in metadata:
            response_time = metadata["response_time"]
            metadata_section += f"- **응답 시간:** {response_time:.2f}초\n"
        
        metadata_section += "\n"
        return metadata_section
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            if isinstance(timestamp_str, str):
                # Handle ISO format timestamps
                if 'T' in timestamp_str:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    return dt.strftime("%Y년 %m월 %d일 %H:%M:%S")
                else:
                    return timestamp_str
            else:
                return str(timestamp_str)
        except Exception:
            return str(timestamp_str)
    
    def _create_footer(self) -> str:
        """Create markdown footer"""
        footer = f"""
---

*이 문서는 HAI Portal에서 자동으로 생성되었습니다.*  
*생성 시간: {datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")}*
"""
        return footer
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get statistics about exported files"""
        try:
            if not os.path.exists(self.export_dir):
                return {"total_files": 0, "total_size": 0, "files": []}
            
            files = []
            total_size = 0
            
            for filename in os.listdir(self.export_dir):
                if filename.endswith('.md'):
                    filepath = os.path.join(self.export_dir, filename)
                    file_size = os.path.getsize(filepath)
                    file_mtime = os.path.getmtime(filepath)
                    
                    files.append({
                        "filename": filename,
                        "size": file_size,
                        "modified": datetime.fromtimestamp(file_mtime).isoformat()
                    })
                    total_size += file_size
            
            return {
                "total_files": len(files),
                "total_size": total_size,
                "files": sorted(files, key=lambda x: x["modified"], reverse=True)
            }
            
        except Exception as e:
            logger.error(f"Error getting export stats: {e}")
            return {"total_files": 0, "total_size": 0, "files": [], "error": str(e)}
