"""
PDF generation service for chat responses
"""
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import tempfile

class PDFService:
    """Service for generating PDF documents from chat responses"""
    
    def __init__(self):
        """Initialize PDF service"""
        self.setup_fonts()
    
    def setup_fonts(self):
        """Setup Korean fonts for PDF generation"""
        try:
            # Try to register Korean fonts if available
            # For now, we'll use default fonts that support basic Korean
            # In a production environment, you would register proper Korean fonts here
            pass
        except Exception as e:
            print(f"Font setup warning: {e}")
    
    def generate_chat_pdf(self, 
                         messages: List[Dict[str, Any]], 
                         session_id: str = "default",
                         session_name: str = "",
                         include_metadata: bool = True) -> bytes:
        """
        Generate PDF from chat messages
        
        Args:
            messages: List of chat messages
            session_id: Session identifier
            session_name: Custom session name
            include_metadata: Whether to include metadata in PDF
            
        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#8B5CF6')
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#666666')
        )
        
        user_style = ParagraphStyle(
            'UserMessage',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor('#F3F4F6'),
            borderColor=colors.HexColor('#8B5CF6'),
            borderWidth=1,
            borderPadding=10
        )
        
        assistant_style = ParagraphStyle(
            'AssistantMessage',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            leftIndent=20,
            rightIndent=20,
            backColor=colors.HexColor('#F8F9FA'),
            borderColor=colors.HexColor('#8B5CF6'),
            borderWidth=1,
            borderPadding=10
        )
        
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.HexColor('#666666')
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph("HAI Portal - 채팅 기록", title_style))
        
        # Subtitle with session info
        session_display = session_name if session_name else f"세션: {session_id}"
        story.append(Paragraph(session_display, subtitle_style))
        
        # Generation timestamp
        story.append(Paragraph(
            f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}", 
            metadata_style
        ))
        
        story.append(Spacer(1, 20))
        
        # Messages
        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            metadata = message.get("metadata", {})
            context = message.get("context", [])
            
            # Role indicator
            if role == "user":
                role_text = "👤 사용자"
                style = user_style
            elif role == "assistant":
                role_text = "🤖 AI 어시스턴트"
                style = assistant_style
            else:
                role_text = f"❓ {role}"
                style = user_style
            
            # Message header
            header_text = f"<b>{role_text}</b>"
            if timestamp:
                header_text += f" • {timestamp}"
            
            story.append(Paragraph(header_text, metadata_style))
            
            # Message content
            # Clean content for PDF (remove HTML tags)
            clean_content = self._clean_content_for_pdf(content)
            story.append(Paragraph(clean_content, style))
            
            # Metadata (if enabled and available)
            if include_metadata and metadata:
                story.append(Spacer(1, 6))
                metadata_text = self._format_metadata_for_pdf(metadata)
                if metadata_text:
                    story.append(Paragraph(f"<b>메타데이터:</b> {metadata_text}", metadata_style))
            
            # Context (if available)
            if context:
                story.append(Spacer(1, 6))
                context_text = self._format_context_for_pdf(context)
                if context_text:
                    story.append(Paragraph(f"<b>참조 문서:</b> {context_text}", metadata_style))
            
            # Add spacing between messages
            if i < len(messages) - 1:
                story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"총 {len(messages)}개의 메시지 • HAI Portal에서 생성됨", 
            metadata_style
        ))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _clean_content_for_pdf(self, content: str) -> str:
        """Clean content for PDF display"""
        if not content:
            return ""
        
        # Remove HTML tags and convert to plain text
        import re
        
        # Remove HTML tags
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # Replace common HTML entities
        clean_content = clean_content.replace('&nbsp;', ' ')
        clean_content = clean_content.replace('&lt;', '<')
        clean_content = clean_content.replace('&gt;', '>')
        clean_content = clean_content.replace('&amp;', '&')
        
        # Clean up whitespace
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        return clean_content
    
    def _format_metadata_for_pdf(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for PDF display"""
        if not metadata:
            return ""
        
        formatted_items = []
        
        for key, value in metadata.items():
            if key == "similarity" and isinstance(value, (int, float)):
                formatted_items.append(f"신뢰도: {value:.1%}")
            elif key == "source" and isinstance(value, str):
                formatted_items.append(f"출처: {value}")
            elif isinstance(value, (str, int, float)):
                formatted_items.append(f"{key}: {value}")
        
        return " • ".join(formatted_items)
    
    def _format_context_for_pdf(self, context: List[Dict[str, Any]]) -> str:
        """Format context for PDF display"""
        if not context:
            return ""
        
        formatted_items = []
        
        for item in context[:3]:  # Limit to first 3 context items
            if isinstance(item, dict):
                source = item.get("source", "Unknown")
                content = item.get("content", "")
                if content:
                    # Truncate long content
                    preview = content[:100] + "..." if len(content) > 100 else content
                    formatted_items.append(f"{source}: {preview}")
            elif isinstance(item, str):
                formatted_items.append(item[:100] + "..." if len(item) > 100 else item)
        
        return " | ".join(formatted_items)
    
    def generate_summary_pdf(self, 
                           messages: List[Dict[str, Any]], 
                           session_id: str = "default",
                           session_name: str = "") -> bytes:
        """
        Generate a summary PDF with key information
        
        Args:
            messages: List of chat messages
            session_id: Session identifier
            session_name: Custom session name
            
        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'SummaryTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=1,
            textColor=colors.HexColor('#8B5CF6')
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph("HAI Portal - 채팅 요약", title_style))
        
        # Session info
        session_display = session_name if session_name else f"세션: {session_id}"
        story.append(Paragraph(session_display, styles['Heading2']))
        story.append(Paragraph(
            f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}", 
            styles['Normal']
        ))
        
        story.append(Spacer(1, 20))
        
        # Statistics
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        
        stats_data = [
            ["항목", "개수"],
            ["총 메시지 수", str(len(messages))],
            ["사용자 메시지", str(len(user_messages))],
            ["AI 응답", str(len(assistant_messages))],
        ]
        
        stats_table = Table(stats_data)
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B5CF6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Key topics (simple keyword extraction)
        all_content = " ".join([msg.get("content", "") for msg in messages])
        key_topics = self._extract_key_topics(all_content)
        
        if key_topics:
            story.append(Paragraph("주요 토픽:", styles['Heading3']))
            for topic in key_topics[:10]:  # Top 10 topics
                story.append(Paragraph(f"• {topic}", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Recent messages preview
        story.append(Paragraph("최근 메시지 미리보기:", styles['Heading3']))
        recent_messages = messages[-5:]  # Last 5 messages
        
        for message in recent_messages:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            role_text = "👤 사용자" if role == "user" else "🤖 AI"
            preview_content = content[:200] + "..." if len(content) > 200 else content
            
            story.append(Paragraph(
                f"<b>{role_text}</b> ({timestamp}): {preview_content}", 
                styles['Normal']
            ))
            story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text (simple implementation)"""
        if not text:
            return []
        
        # Simple keyword extraction (in a real implementation, you'd use NLP libraries)
        import re
        
        # Remove common words and extract potential keywords
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common words
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            '한국어', '입니다', '합니다', '있습니다', '됩니다', '입니다', '입니다', '입니다'
        }
        
        # Count word frequency
        word_count = {}
        for word in words:
            if len(word) > 2 and word not in common_words:
                word_count[word] = word_count.get(word, 0) + 1
        
        # Return top words
        return sorted(word_count.keys(), key=lambda x: word_count[x], reverse=True)
