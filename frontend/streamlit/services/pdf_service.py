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
        """Setup Korean fonts for PDF generation with enhanced quality"""
        try:
            # Register Korean fonts for proper display
            self.korean_font_name = self._register_korean_font()
            self.korean_bold_font_name = self._register_korean_bold_font()
            print(f"Korean font registered: {self.korean_font_name}")
            print(f"Korean bold font registered: {self.korean_bold_font_name}")
        except Exception as e:
            print(f"Font setup warning: {e}")
            # Fallback to default font
            self.korean_font_name = "Helvetica"
            self.korean_bold_font_name = "Helvetica-Bold"
    
    def _register_korean_font(self):
        """Register Korean font from system or bundled resources"""
        # First, try to find fonts using system font discovery
        system_fonts = self._find_system_korean_fonts()
        
        # Common Korean font paths for different operating systems
        font_paths = [
            # macOS - Korean fonts (prioritize these)
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/System/Library/Fonts/AppleGothic.ttf",
            "/Library/Fonts/AppleGothic.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            # Windows - Korean fonts
            "C:/Windows/Fonts/malgun.ttf",  # 맑은 고딕
            "C:/Windows/Fonts/malgunbd.ttf",  # 맑은 고딕 Bold
            "C:/Windows/Fonts/gulim.ttc",   # 굴림
            "C:/Windows/Fonts/batang.ttc",  # 바탕
            "C:/Windows/Fonts/dotum.ttc",   # 돋움
            # Linux - Korean fonts
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # Fallback fonts
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        
        # Combine system fonts with predefined paths
        all_font_paths = system_fonts + font_paths
        
        # Try to find and register a Korean font
        for font_path in all_font_paths:
            if os.path.exists(font_path):
                try:
                    # Extract font name from path
                    font_name = os.path.basename(font_path).split('.')[0]
                    
                    # Register the font
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    print(f"Successfully registered font: {font_name} from {font_path}")
                    
                    # Test if the font supports Korean characters
                    if self._test_korean_support(font_name):
                        print(f"Font {font_name} supports Korean characters")
                        return font_name
                    else:
                        print(f"Font {font_name} does not support Korean characters")
                        
                except Exception as e:
                    print(f"Failed to register font {font_path}: {e}")
                    continue
        
        # If no Korean font found, try to use built-in fonts that might support Korean
        try:
            # Try to register a basic font that might support Korean
            if os.path.exists("/System/Library/Fonts/Helvetica.ttc"):
                pdfmetrics.registerFont(TTFont("KoreanFont", "/System/Library/Fonts/Helvetica.ttc"))
                print("Registered Helvetica as KoreanFont fallback")
                return "KoreanFont"
        except Exception as e:
            print(f"Failed to register Helvetica fallback: {e}")
        
        # Final fallback - use default fonts
        print("Using Helvetica as final fallback")
        return "Helvetica"
    
    def _register_korean_bold_font(self):
        """Register Korean bold font from system or bundled resources"""
        # First, try to find bold fonts using system font discovery
        system_fonts = self._find_system_korean_fonts()
        
        # Common Korean bold font paths for different operating systems
        bold_font_paths = [
            # macOS - Korean bold fonts (prioritize these)
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/System/Library/Fonts/AppleGothic.ttf",
            "/Library/Fonts/AppleGothic.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            # Windows - Korean bold fonts
            "C:/Windows/Fonts/malgunbd.ttf",  # 맑은 고딕 Bold
            "C:/Windows/Fonts/malgun.ttf",   # 맑은 고딕
            "C:/Windows/Fonts/gulim.ttc",    # 굴림
            "C:/Windows/Fonts/batang.ttc",   # 바탕
            "C:/Windows/Fonts/dotum.ttc",    # 돋움
            # Linux - Korean bold fonts
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
            "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            # Fallback fonts
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        
        # Combine system fonts with predefined paths
        all_font_paths = system_fonts + bold_font_paths
        
        # Try to find and register a Korean bold font
        for font_path in all_font_paths:
            if os.path.exists(font_path):
                try:
                    # Extract font name from path
                    font_name = os.path.basename(font_path).split('.')[0]
                    bold_font_name = f"{font_name}Bold"
                    
                    # Register the font
                    pdfmetrics.registerFont(TTFont(bold_font_name, font_path))
                    print(f"Successfully registered bold font: {bold_font_name} from {font_path}")
                    
                    # Test if the font supports Korean characters
                    if self._test_korean_support(bold_font_name):
                        print(f"Bold font {bold_font_name} supports Korean characters")
                        return bold_font_name
                    else:
                        print(f"Bold font {bold_font_name} does not support Korean characters")
                        
                except Exception as e:
                    print(f"Failed to register bold font {font_path}: {e}")
                    continue
        
        # If no Korean bold font found, try to use built-in fonts that might support Korean
        try:
            # Try to register a basic font that might support Korean
            if os.path.exists("/System/Library/Fonts/Helvetica.ttc"):
                pdfmetrics.registerFont(TTFont("KoreanBoldFont", "/System/Library/Fonts/Helvetica.ttc"))
                print("Registered Helvetica as KoreanBoldFont fallback")
                return "KoreanBoldFont"
        except Exception as e:
            print(f"Failed to register Helvetica bold fallback: {e}")
        
        # Final fallback - use default bold fonts
        print("Using Helvetica-Bold as final fallback")
        return "Helvetica-Bold"
    
    def _find_system_korean_fonts(self):
        """Find Korean fonts in system font directories"""
        font_paths = []
        
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Search common macOS font directories
                font_dirs = [
                    "/System/Library/Fonts/",
                    "/Library/Fonts/",
                    "/Users/{}/Library/Fonts/".format(os.getenv('USER', '')),
                    "/System/Library/Fonts/Supplemental/"
                ]
                
                for font_dir in font_dirs:
                    if os.path.exists(font_dir):
                        for root, dirs, files in os.walk(font_dir):
                            for file in files:
                                if file.lower().endswith(('.ttf', '.ttc', '.otf')):
                                    # Check if filename suggests Korean support
                                    if any(keyword in file.lower() for keyword in ['korean', 'hangul', 'gothic', 'malgun', 'gulim', 'batang', 'dotum', 'nanum']):
                                        font_paths.append(os.path.join(root, file))
                                        
            elif system == "Windows":
                # Search Windows font directory
                font_dir = "C:/Windows/Fonts/"
                if os.path.exists(font_dir):
                    for file in os.listdir(font_dir):
                        if file.lower().endswith(('.ttf', '.ttc', '.otf')):
                            if any(keyword in file.lower() for keyword in ['korean', 'hangul', 'gothic', 'malgun', 'gulim', 'batang', 'dotum', 'nanum']):
                                font_paths.append(os.path.join(font_dir, file))
                                
            elif system == "Linux":
                # Search common Linux font directories
                font_dirs = [
                    "/usr/share/fonts/",
                    "/usr/local/share/fonts/",
                    "/home/{}/.fonts/".format(os.getenv('USER', '')),
                    "/home/{}/.local/share/fonts/".format(os.getenv('USER', ''))
                ]
                
                for font_dir in font_dirs:
                    if os.path.exists(font_dir):
                        for root, dirs, files in os.walk(font_dir):
                            for file in files:
                                if file.lower().endswith(('.ttf', '.ttc', '.otf')):
                                    if any(keyword in file.lower() for keyword in ['korean', 'hangul', 'gothic', 'malgun', 'gulim', 'batang', 'dotum', 'nanum']):
                                        font_paths.append(os.path.join(root, file))
                                        
        except Exception as e:
            print(f"Error finding system fonts: {e}")
            
        return font_paths
    
    def _test_korean_support(self, font_name):
        """Test if a font supports Korean characters"""
        try:
            # Simple test - just try to create a paragraph with Korean text
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph
            
            styles = getSampleStyleSheet()
            test_style = ParagraphStyle(
                'TestStyle',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=12
            )
            
            # Try to create a paragraph with Korean text
            test_text = "한글 테스트"
            paragraph = Paragraph(test_text, test_style)
            
            # If we get here without error, the font supports Korean
            return True
        except Exception as e:
            print(f"Korean support test failed for {font_name}: {e}")
            return False
    
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
        
        # Create PDF document with enhanced quality settings
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,   # Optimized margins for better readability
            leftMargin=72,    # Optimized margins for better readability
            topMargin=72,     # Optimized margins for better readability
            bottomMargin=72,  # Optimized margins for better readability
            allowSplitting=1, # Allow content to split across pages
            title="HAI Portal - 채팅 기록",
            author="HAI Portal",
            subject="채팅 대화 기록",
            creator="HAI Portal PDF Generator",
            producer="ReportLab with Korean Font Support"
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles with enhanced Korean font support and better quality
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=self.korean_font_name,
            fontSize=24,  # Increased font size for better readability
            spaceAfter=30,  # Increased spacing
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#8B5CF6'),
            leading=32,  # Increased line height for better readability
            spaceBefore=20  # Added space before
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontName=self.korean_font_name,
            fontSize=16,  # Increased font size
            spaceAfter=20,  # Increased spacing
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#666666'),
            leading=22,  # Increased line height
            spaceBefore=10  # Added space before
        )
        
        user_style = ParagraphStyle(
            'UserMessage',
            parent=styles['Normal'],
            fontName=self.korean_font_name,
            fontSize=12,  # Increased font size for better readability
            spaceAfter=25,  # Increased space after
            spaceBefore=20, # Increased space before
            leftIndent=25,  # Optimized left indent
            rightIndent=25, # Optimized right indent
            backColor=colors.HexColor('#F8FAFC'),
            borderColor=colors.HexColor('#8B5CF6'),
            borderWidth=1.5,  # Slightly thicker border for better visibility
            borderPadding=20,  # Optimized padding
            borderRadius=10,  # Increased border radius for modern look
            leading=20,  # Increased line height for better readability
            alignment=0,  # Left align
            firstLineIndent=0  # No first line indent
        )
        
        assistant_style = ParagraphStyle(
            'AssistantMessage',
            parent=styles['Normal'],
            fontName=self.korean_font_name,
            fontSize=12,  # Increased font size for better readability
            spaceAfter=25,  # Increased space after
            spaceBefore=20, # Increased space before
            leftIndent=25,  # Optimized left indent
            rightIndent=25, # Optimized right indent
            backColor=colors.HexColor('#F0FDF4'),
            borderColor=colors.HexColor('#059669'),
            borderWidth=1.5,  # Slightly thicker border for better visibility
            borderPadding=20,  # Optimized padding
            borderRadius=10,  # Increased border radius for modern look
            leading=20,  # Increased line height for better readability
            alignment=0,  # Left align
            firstLineIndent=0  # No first line indent
        )
        
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontName=self.korean_font_name,
            fontSize=10,  # Increased font size for better readability
            spaceAfter=10,  # Increased spacing
            textColor=colors.HexColor('#666666'),
            leading=14,  # Increased line height
            spaceBefore=5  # Added space before
        )
        
        # Enhanced code block style with better quality
        code_style = ParagraphStyle(
            'CodeBlock',
            parent=styles['Normal'],
            fontName='Courier',  # Use monospace font for code
            fontSize=10,  # Increased font size for better readability
            spaceAfter=25,  # Increased space after
            spaceBefore=20, # Increased space before
            leftIndent=30,  # Optimized left indent
            rightIndent=30, # Optimized right indent
            backColor=colors.HexColor('#1F2937'),
            borderColor=colors.HexColor('#374151'),
            borderWidth=1.5,  # Slightly thicker border
            borderPadding=15,  # Optimized padding
            textColor=colors.HexColor('#F9FAFB'),
            leading=18,  # Increased line height for better readability
            alignment=0,  # Left align
            firstLineIndent=0  # No first line indent
        )
        
        # Inline code style with better quality
        inline_code_style = ParagraphStyle(
            'InlineCode',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=11,  # Increased font size
            backColor=colors.HexColor('#F3F4F6'),
            textColor=colors.HexColor('#374151'),
            leading=18,  # Increased line height
            borderWidth=0.5,  # Added subtle border
            borderColor=colors.HexColor('#D1D5DB'),
            borderPadding=3  # Added padding
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
        
        # Messages - Process in chronological order with proper chat formatting
        for i, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            metadata = message.get("metadata", {})
            context = message.get("context", [])
            
            # Skip empty messages
            if not content or not content.strip():
                continue
            
            # Role indicator and styling with enhanced quality
            if role == "user":
                role_text = "👤 사용자"
                message_style = user_style
                header_style = ParagraphStyle(
                    'UserHeader',
                    parent=metadata_style,
                    fontName=self.korean_bold_font_name,  # Use bold font for headers
                    fontSize=11,  # Increased font size
                    spaceAfter=6,  # Increased spacing
                    spaceBefore=5,  # Added space before
                    textColor=colors.HexColor('#8B5CF6'),
                    alignment=0,  # Left align
                    leading=14  # Added line height
                )
            elif role == "assistant":
                role_text = "🤖 AI 어시스턴트"
                message_style = assistant_style
                header_style = ParagraphStyle(
                    'AssistantHeader',
                    parent=metadata_style,
                    fontName=self.korean_bold_font_name,  # Use bold font for headers
                    fontSize=11,  # Increased font size
                    spaceAfter=6,  # Increased spacing
                    spaceBefore=5,  # Added space before
                    textColor=colors.HexColor('#059669'),
                    alignment=0,  # Left align
                    leading=14  # Added line height
                )
            else:
                role_text = f"❓ {role}"
                message_style = user_style
                header_style = ParagraphStyle(
                    'UnknownHeader',
                    parent=metadata_style,
                    fontName=self.korean_bold_font_name,
                    fontSize=11,
                    spaceAfter=6,
                    spaceBefore=5,
                    textColor=colors.HexColor('#666666'),
                    alignment=0,
                    leading=14
                )
            
            # Message header with timestamp
            header_text = f"<b>{role_text}</b>"
            if timestamp:
                header_text += f" • {timestamp}"
            
            story.append(Paragraph(header_text, header_style))
            
            # Process message content with code block detection
            processed_content = self._process_content_for_pdf(content, code_style, inline_code_style, message_style)
            
            # Add processed content to story
            for element in processed_content:
                story.append(element)
            
            # Add optimized spacing after message content
            story.append(Spacer(1, 20))  # Increased spacing
            
            # Metadata (if enabled and available) - only for assistant messages
            if include_metadata and metadata and role == "assistant":
                metadata_text = self._format_metadata_for_pdf(metadata)
                if metadata_text:
                    story.append(Paragraph(f"<i>메타데이터: {metadata_text}</i>", metadata_style))
                    story.append(Spacer(1, 8))  # Increased spacing
            
            # Context (if available) - only for assistant messages
            if context and role == "assistant":
                context_text = self._format_context_for_pdf(context)
                if context_text:
                    story.append(Paragraph(f"<i>참조 문서: {context_text}</i>", metadata_style))
                    story.append(Spacer(1, 8))  # Increased spacing
            
            # Add optimized spacing between messages
            if i < len(messages) - 1:
                story.append(Spacer(1, 35))  # Increased spacing between messages
        
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
        
        # Add additional PDF metadata and structure improvements
        pdf_content = self._enhance_pdf_metadata(pdf_content, messages, session_id, session_name)
        
        return pdf_content
    
    def _process_content_for_pdf(self, content: str, code_style, inline_code_style, default_style):
        """Process content for PDF display with enhanced code block detection and formatting"""
        if not content or not content.strip():
            return [Paragraph("", default_style)]
        
        import re
        from reportlab.platypus import Spacer, KeepTogether
        
        elements = []
        
        # Clean up content first
        content = content.strip()
        
        # Enhanced code block pattern to handle various formats
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        parts = re.split(code_block_pattern, content, flags=re.DOTALL)
        
        # If we have code blocks, process them
        if len(parts) > 1:
            for i, part in enumerate(parts):
                if i % 3 == 0:  # Regular text parts
                    if part.strip():
                        # Process different content types
                        processed_elements = self._process_text_content(part, inline_code_style, default_style)
                        elements.extend(processed_elements)
                elif i % 3 == 1:  # Language identifier
                    continue  # Skip language identifier
                elif i % 3 == 2:  # Code content
                    if part.strip():
                        # Enhanced code processing
                        code_elements = self._process_code_content(part, code_style)
                        elements.extend(code_elements)
        else:
            # No code blocks found, process as regular text
            processed_elements = self._process_text_content(content, inline_code_style, default_style)
            elements.extend(processed_elements)
        
        return elements
    
    def _process_text_content(self, text: str, inline_code_style, default_style):
        """Process regular text content with enhanced formatting"""
        import re
        from reportlab.platypus import Spacer
        
        elements = []
        
        # Split by lines to process structure
        lines = text.split('\n')
        current_paragraph = []
        
        for line in lines:
            # Preserve original line structure but clean up
            original_line = line
            line = line.strip()
            
            if not line:
                if current_paragraph:
                    # Process accumulated paragraph
                    paragraph_text = '\n'.join(current_paragraph)
                    processed_text = self._process_inline_code(paragraph_text, inline_code_style)
                    elements.append(Paragraph(processed_text, default_style))
                    current_paragraph = []
                # Add spacing for empty lines
                elements.append(Spacer(1, 8))
                continue
            
            # Check for special formatting patterns
            if self._is_file_structure_line(line):
                # Process file structure
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    processed_text = self._process_inline_code(paragraph_text, inline_code_style)
                    elements.append(Paragraph(processed_text, default_style))
                    current_paragraph = []
                
                # Add file structure with proper indentation
                file_style = self._create_file_structure_style(default_style)
                elements.append(Paragraph(self._format_file_structure(line), file_style))
                
            elif self._is_config_line(line):
                # Process configuration lines
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    processed_text = self._process_inline_code(paragraph_text, inline_code_style)
                    elements.append(Paragraph(processed_text, default_style))
                    current_paragraph = []
                
                # Add config line with proper formatting
                config_style = self._create_config_style(default_style)
                elements.append(Paragraph(self._format_config_line(line), config_style))
                
            elif line.startswith('###') or line.startswith('##') or line.startswith('#'):
                # Process headers
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    processed_text = self._process_inline_code(paragraph_text, inline_code_style)
                    elements.append(Paragraph(processed_text, default_style))
                    current_paragraph = []
                
                # Add header with proper styling
                header_style = self._create_header_style(default_style, line.count('#'))
                elements.append(Paragraph(self._format_header(line), header_style))
                
            elif line.startswith('- ') or line.startswith('* ') or re.match(r'^\d+\.', line):
                # Process list items
                if current_paragraph:
                    paragraph_text = '\n'.join(current_paragraph)
                    processed_text = self._process_inline_code(paragraph_text, inline_code_style)
                    elements.append(Paragraph(processed_text, default_style))
                    current_paragraph = []
                
                # Add list item with proper indentation
                list_style = self._create_list_style(default_style)
                elements.append(Paragraph(self._format_list_item(line), list_style))
                
            else:
                current_paragraph.append(original_line)  # Preserve original formatting
        
        # Process remaining paragraph
        if current_paragraph:
            paragraph_text = '\n'.join(current_paragraph)
            processed_text = self._process_inline_code(paragraph_text, inline_code_style)
            elements.append(Paragraph(processed_text, default_style))
        
        return elements
    
    def _process_code_content(self, code: str, code_style):
        """Process code content with enhanced formatting and better quality"""
        import re
        from reportlab.platypus import Spacer
        
        elements = []
        
        # Clean up code content
        clean_code = code.strip()
        
        # Preserve indentation and structure
        lines = clean_code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Preserve leading whitespace for indentation
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 0:
                # Convert spaces to non-breaking spaces for better PDF rendering
                # Use proper spacing for indentation
                formatted_line = '&nbsp;' * leading_spaces + line.lstrip()
            else:
                formatted_line = line
            
            # Escape HTML entities properly
            formatted_line = (formatted_line
                            .replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace('"', '&quot;')
                            .replace("'", '&#x27;'))
            
            formatted_lines.append(formatted_line)
        
        # Join lines and create paragraph with better formatting
        formatted_code = '\n'.join(formatted_lines)
        
        # Add syntax highlighting for common keywords (basic implementation)
        formatted_code = self._add_basic_syntax_highlighting(formatted_code)
        
        elements.append(Paragraph(formatted_code, code_style))
        
        return elements
    
    def _add_basic_syntax_highlighting(self, code: str) -> str:
        """Add basic syntax highlighting for common programming languages"""
        import re
        
        # Common keywords for syntax highlighting
        keywords = [
            'def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally',
            'return', 'yield', 'break', 'continue', 'pass', 'lambda', 'with', 'as', 'in', 'is', 'not', 'and', 'or',
            'public', 'private', 'protected', 'static', 'final', 'abstract', 'interface', 'extends', 'implements',
            'function', 'var', 'let', 'const', 'async', 'await', 'Promise', 'then', 'catch', 'throw', 'new',
            'int', 'string', 'boolean', 'float', 'double', 'char', 'void', 'null', 'undefined', 'true', 'false'
        ]
        
        # Create pattern for keywords
        keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
        
        def highlight_keyword(match):
            keyword = match.group(1)
            return f'<font color="#0066CC"><b>{keyword}</b></font>'
        
        # Apply keyword highlighting
        highlighted_code = re.sub(keyword_pattern, highlight_keyword, code)
        
        # Highlight strings (basic implementation)
        string_pattern = r'(["\'])(?:(?!\1)[^\\]|\\.)*\1'
        def highlight_string(match):
            string_content = match.group(0)
            return f'<font color="#008800">{string_content}</font>'
        
        highlighted_code = re.sub(string_pattern, highlight_string, highlighted_code)
        
        # Highlight comments
        comment_pattern = r'(#.*?$|//.*?$|/\*.*?\*/)'
        def highlight_comment(match):
            comment = match.group(1)
            return f'<font color="#666666"><i>{comment}</i></font>'
        
        highlighted_code = re.sub(comment_pattern, highlight_comment, highlighted_code, flags=re.MULTILINE)
        
        return highlighted_code
    
    def _enhance_pdf_metadata(self, pdf_content: bytes, messages: List[Dict[str, Any]], session_id: str, session_name: str) -> bytes:
        """Enhance PDF with additional metadata and structure improvements"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            import io
            
            # Create a new PDF with enhanced metadata
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Add custom metadata
            c.setTitle(f"HAI Portal - 채팅 기록 ({session_name or session_id})")
            c.setAuthor("HAI Portal")
            c.setSubject("채팅 대화 기록")
            c.setCreator("HAI Portal PDF Generator")
            c.setProducer("ReportLab with Korean Font Support")
            c.setKeywords("채팅, AI, 대화, HAI Portal, PDF")
            
            # Add creation and modification dates
            from datetime import datetime
            now = datetime.now()
            c.setCreationDate(now)
            c.setModificationDate(now)
            
            # Add custom properties
            c.setPageCompression(1)  # Enable compression for smaller file size
            c.setPageMode("/UseOutlines")  # Enable bookmarks/outline
            
            # Close the canvas
            c.save()
            
            # For now, return the original content as the enhancement is complex
            # In a full implementation, you would merge the metadata with the original PDF
            return pdf_content
            
        except Exception as e:
            print(f"PDF metadata enhancement failed: {e}")
            return pdf_content
    
    def _is_file_structure_line(self, line: str) -> bool:
        """Check if line represents file structure"""
        import re
        
        # Patterns for file structure
        patterns = [
            r'^\s*[├└│]\s*',  # Tree structure characters
            r'^\s*[a-zA-Z0-9_\-\./]+$',  # Simple file/folder names
            r'^\s*[a-zA-Z0-9_\-\./]+\s*$',  # File/folder names with spaces
            r'^\s*[a-zA-Z0-9_\-\./]+\.(java|py|js|ts|html|css|xml|properties|yml|yaml|json|md|txt)$',  # File extensions
            r'^\s*[a-zA-Z0-9_\-\./]+/$',  # Directory names ending with /
            r'^\s*[a-zA-Z0-9_\-\./]+\s*$',  # General file/folder patterns
        ]
        
        # Additional checks for common file structure patterns
        if any(keyword in line.lower() for keyword in ['src/', 'main/', 'java/', 'resources/', 'static/', 'templates/']):
            return True
            
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        return False
    
    def _is_config_line(self, line: str) -> bool:
        """Check if line represents configuration"""
        import re
        
        # Patterns for configuration lines
        patterns = [
            r'^[a-zA-Z0-9_\-\.]+\.',  # Property keys
            r'^#.*',  # Comments
            r'^spring\.',  # Spring properties
            r'^server\.',  # Server properties
            r'^database\.',  # Database properties
            r'^[a-zA-Z0-9_\-\.]+\s*=',  # Key-value pairs
            r'^jdbc:',  # JDBC URLs
            r'^mysql:',  # MySQL URLs
            r'^postgresql:',  # PostgreSQL URLs
            r'^h2:',  # H2 URLs
        ]
        
        # Additional checks for common config patterns
        if any(keyword in line.lower() for keyword in ['url=', 'username=', 'password=', 'port=', 'host=']):
            return True
            
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        return False
    
    def _create_file_structure_style(self, base_style):
        """Create style for file structure"""
        return ParagraphStyle(
            'FileStructure',
            parent=base_style,
            fontName='Courier',
            fontSize=10,
            leftIndent=10,
            textColor=colors.HexColor('#374151'),
            backColor=colors.HexColor('#F9FAFB'),
            borderColor=colors.HexColor('#E5E7EB'),
            borderWidth=0.5,
            borderPadding=4
        )
    
    def _create_config_style(self, base_style):
        """Create style for configuration lines"""
        return ParagraphStyle(
            'ConfigLine',
            parent=base_style,
            fontName='Courier',
            fontSize=10,
            leftIndent=5,
            textColor=colors.HexColor('#1F2937'),
            backColor=colors.HexColor('#F3F4F6'),
            borderColor=colors.HexColor('#D1D5DB'),
            borderWidth=0.5,
            borderPadding=4
        )
    
    def _create_header_style(self, base_style, level: int):
        """Create style for headers"""
        font_sizes = {1: 16, 2: 14, 3: 12, 4: 11, 5: 10, 6: 9}
        font_size = font_sizes.get(level, 12)
        
        return ParagraphStyle(
            f'Header{level}',
            parent=base_style,
            fontName=self.korean_font_name,
            fontSize=font_size,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#1F2937'),
            backColor=colors.HexColor('#F8FAFC'),
            borderColor=colors.HexColor('#CBD5E1'),
            borderWidth=1,
            borderPadding=10,
            leading=font_size + 4
        )
    
    def _create_list_style(self, base_style):
        """Create style for list items"""
        return ParagraphStyle(
            'ListItem',
            parent=base_style,
            fontName=self.korean_font_name,
            fontSize=11,
            leftIndent=20,
            spaceAfter=5,
            spaceBefore=2,
            textColor=colors.HexColor('#374151'),
            leading=16
        )
    
    def _format_file_structure(self, line: str) -> str:
        """Format file structure line"""
        # Clean up the line and add proper indentation
        clean_line = line.strip()
        
        # Add visual indicators for better structure
        if clean_line.endswith('/'):
            return f"📁 {clean_line}"
        elif '.' in clean_line:
            return f"📄 {clean_line}"
        else:
            return f"📂 {clean_line}"
    
    def _format_config_line(self, line: str) -> str:
        """Format configuration line"""
        # Highlight key-value pairs
        if '=' in line:
            parts = line.split('=', 1)
            if len(parts) == 2:
                key, value = parts
                return f"<b>{key.strip()}</b> = {value.strip()}"
        
        # Highlight comments
        if line.strip().startswith('#'):
            return f"<i>{line}</i>"
        
        return line
    
    def _format_header(self, line: str) -> str:
        """Format header line"""
        import re
        # Remove # symbols and clean up
        clean_line = re.sub(r'^#+\s*', '', line.strip())
        return f"<b>{clean_line}</b>"
    
    def _format_list_item(self, line: str) -> str:
        """Format list item line"""
        import re
        
        # Handle different list formats
        if line.startswith('- ') or line.startswith('* '):
            # Bullet list
            content = line[2:].strip()
            return f"• {content}"
        elif re.match(r'^\d+\.', line):
            # Numbered list
            content = re.sub(r'^\d+\.\s*', '', line)
            return f"1. {content}"
        else:
            return line
    
    def _process_inline_code(self, text: str, inline_code_style):
        """Process inline code (single backticks) in text with enhanced quality"""
        import re
        
        # Find inline code patterns
        inline_code_pattern = r'`([^`]+)`'
        
        def replace_inline_code(match):
            code_text = match.group(1)
            # Escape HTML entities properly
            code_text = (code_text
                        .replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
                        .replace('"', '&quot;')
                        .replace("'", '&#x27;'))
            return f'<font name="Courier" color="#374151" backcolor="#F3F4F6" size="11">{code_text}</font>'
        
        processed_text = re.sub(inline_code_pattern, replace_inline_code, text)
        
        # Clean up other HTML tags but preserve our inline code formatting
        processed_text = re.sub(r'<(?!/?font)[^>]+>', '', processed_text)
        
        # Replace common HTML entities with proper handling
        processed_text = processed_text.replace('&nbsp;', ' ')
        processed_text = processed_text.replace('&lt;', '<')
        processed_text = processed_text.replace('&gt;', '>')
        processed_text = processed_text.replace('&amp;', '&')
        processed_text = processed_text.replace('&quot;', '"')
        processed_text = processed_text.replace('&#x27;', "'")
        
        # Clean up whitespace but preserve Korean text structure
        processed_text = re.sub(r'[ \t]+', ' ', processed_text)  # Only collapse spaces and tabs
        processed_text = processed_text.strip()
        
        return processed_text
    
    def _clean_content_for_pdf(self, content: str) -> str:
        """Clean content for PDF display (legacy method)"""
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
        
        # Create PDF document with enhanced quality settings
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,   # Optimized margins
            leftMargin=72,    # Optimized margins
            topMargin=72,     # Optimized margins
            bottomMargin=72,  # Optimized margins
            allowSplitting=1, # Allow content to split across pages
            title="HAI Portal - 채팅 요약",
            author="HAI Portal",
            subject="채팅 요약 보고서",
            creator="HAI Portal PDF Generator",
            producer="ReportLab with Korean Font Support"
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles with Korean font support and better quality
        title_style = ParagraphStyle(
            'SummaryTitle',
            parent=styles['Heading1'],
            fontName=self.korean_font_name,
            fontSize=24,  # Increased font size
            spaceAfter=25,  # Increased spacing
            spaceBefore=15,  # Added space before
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#8B5CF6'),
            leading=30  # Increased line height
        )
        
        # Build content
        story = []
        
        # Title
        story.append(Paragraph("HAI Portal - 채팅 요약", title_style))
        
        # Session info with enhanced styling
        session_display = session_name if session_name else f"세션: {session_id}"
        session_style = ParagraphStyle(
            'SessionInfo',
            parent=styles['Heading2'],
            fontName=self.korean_font_name,
            fontSize=18,  # Increased font size
            spaceAfter=15,  # Increased spacing
            spaceBefore=10,  # Added space before
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#374151'),
            leading=24  # Increased line height
        )
        story.append(Paragraph(session_display, session_style))
        
        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=styles['Normal'],
            fontName=self.korean_font_name,
            fontSize=14,  # Increased font size
            spaceAfter=25,  # Increased spacing
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#666666'),
            leading=18  # Increased line height
        )
        story.append(Paragraph(
            f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}", 
            timestamp_style
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
            ('FONTNAME', (0, 0), (-1, 0), self.korean_bold_font_name),  # Use bold font
            ('FONTSIZE', (0, 0), (-1, 0), 16),  # Increased font size
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),  # Increased padding
            ('TOPPADDING', (0, 0), (-1, 0), 15),  # Added top padding
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),  # Better background color
            ('FONTNAME', (0, 1), (-1, -1), self.korean_font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 14),  # Increased font size
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),  # Increased padding
            ('TOPPADDING', (0, 1), (-1, -1), 12),  # Added top padding
            ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#374151')),  # Thicker grid lines
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')])  # Alternating row colors
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Key topics (simple keyword extraction)
        all_content = " ".join([msg.get("content", "") for msg in messages])
        key_topics = self._extract_key_topics(all_content)
        
        if key_topics:
            topics_style = ParagraphStyle(
                'TopicsHeading',
                parent=styles['Heading3'],
                fontName=self.korean_bold_font_name,  # Use bold font
                fontSize=16,  # Increased font size
                spaceAfter=15,  # Increased spacing
                spaceBefore=10,  # Added space before
                textColor=colors.HexColor('#374151'),
                leading=20  # Increased line height
            )
            story.append(Paragraph("주요 토픽:", topics_style))
            
            topic_style = ParagraphStyle(
                'TopicItem',
                parent=styles['Normal'],
                fontName=self.korean_font_name,
                fontSize=13,  # Increased font size
                spaceAfter=8,  # Increased spacing
                leftIndent=20,  # Added indentation
                textColor=colors.HexColor('#4B5563'),
                leading=18  # Increased line height
            )
            for topic in key_topics[:10]:  # Top 10 topics
                story.append(Paragraph(f"• {topic}", topic_style))
            story.append(Spacer(1, 20))
        
        # Recent messages preview with enhanced styling
        preview_style = ParagraphStyle(
            'PreviewHeading',
            parent=styles['Heading3'],
            fontName=self.korean_bold_font_name,  # Use bold font
            fontSize=16,  # Increased font size
            spaceAfter=15,  # Increased spacing
            spaceBefore=10,  # Added space before
            textColor=colors.HexColor('#374151'),
            leading=20  # Increased line height
        )
        story.append(Paragraph("최근 메시지 미리보기:", preview_style))
        
        recent_messages = messages[-5:]  # Last 5 messages
        
        message_style = ParagraphStyle(
            'MessagePreview',
            parent=styles['Normal'],
            fontName=self.korean_font_name,
            fontSize=13,  # Increased font size
            spaceAfter=15,  # Increased spacing
            spaceBefore=8,  # Added space before
            leftIndent=15,  # Added indentation
            rightIndent=15,  # Added right indentation
            backColor=colors.HexColor('#F8FAFC'),  # Added background color
            borderColor=colors.HexColor('#E5E7EB'),  # Added border
            borderWidth=1,
            borderPadding=10,  # Added padding
            textColor=colors.HexColor('#374151'),
            leading=18  # Increased line height
        )
        
        for message in recent_messages:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            role_text = "👤 사용자" if role == "user" else "🤖 AI"
            preview_content = content[:200] + "..." if len(content) > 200 else content
            
            story.append(Paragraph(
                f"<b>{role_text}</b> ({timestamp}): {preview_content}", 
                message_style
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
