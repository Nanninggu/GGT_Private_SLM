"""
File processing service for extracting text from various file formats
"""
import io
import logging
from typing import Dict, Any, Optional
import PyPDF2
from docx import Document
import pandas as pd
import json

logger = logging.getLogger(__name__)

class FileProcessingService:
    """Service for processing various file formats and extracting text"""
    
    @staticmethod
    def extract_text_from_file(file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """
        Extract text content from various file formats
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Get file extension
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            
            # Extract text based on file type
            if content_type == 'application/pdf' or file_ext == 'pdf':
                return FileProcessingService._extract_from_pdf(file_content, filename)
            elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_ext == 'docx':
                return FileProcessingService._extract_from_docx(file_content, filename)
            elif content_type == 'text/csv' or file_ext == 'csv':
                return FileProcessingService._extract_from_csv(file_content, filename)
            elif content_type == 'application/json' or file_ext == 'json':
                return FileProcessingService._extract_from_json(file_content, filename)
            elif content_type.startswith('text/') or file_ext in ['txt', 'md']:
                return FileProcessingService._extract_from_text(file_content, filename)
            else:
                # Try to decode as text for unknown types
                return FileProcessingService._extract_from_text(file_content, filename)
                
        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {e}")
            return {
                "text": "",
                "metadata": {
                    "filename": filename,
                    "content_type": content_type,
                    "error": str(e),
                    "extraction_method": "failed"
                }
            }
    
    @staticmethod
    def _extract_from_pdf(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            page_count = len(pdf_reader.pages)
            
            for page_num in range(page_count):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
            
            return {
                "text": text_content.strip(),
                "metadata": {
                    "filename": filename,
                    "content_type": "application/pdf",
                    "page_count": page_count,
                    "extraction_method": "pdf",
                    "size": len(file_content)
                }
            }
        except Exception as e:
            logger.error(f"PDF extraction failed for {filename}: {e}")
            return {
                "text": "",
                "metadata": {
                    "filename": filename,
                    "content_type": "application/pdf",
                    "error": str(e),
                    "extraction_method": "pdf_failed"
                }
            }
    
    @staticmethod
    def _extract_from_docx(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from DOCX file"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            text_content = ""
            paragraph_count = 0
            
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
                paragraph_count += 1
            
            return {
                "text": text_content.strip(),
                "metadata": {
                    "filename": filename,
                    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "paragraph_count": paragraph_count,
                    "extraction_method": "docx",
                    "size": len(file_content)
                }
            }
        except Exception as e:
            logger.error(f"DOCX extraction failed for {filename}: {e}")
            return {
                "text": "",
                "metadata": {
                    "filename": filename,
                    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "error": str(e),
                    "extraction_method": "docx_failed"
                }
            }
    
    @staticmethod
    def _extract_from_csv(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from CSV file"""
        try:
            csv_text = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_text))
            
            # Convert DataFrame to text
            text_content = df.to_string(index=False)
            
            return {
                "text": text_content,
                "metadata": {
                    "filename": filename,
                    "content_type": "text/csv",
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns),
                    "extraction_method": "csv",
                    "size": len(file_content)
                }
            }
        except Exception as e:
            logger.error(f"CSV extraction failed for {filename}: {e}")
            return {
                "text": "",
                "metadata": {
                    "filename": filename,
                    "content_type": "text/csv",
                    "error": str(e),
                    "extraction_method": "csv_failed"
                }
            }
    
    @staticmethod
    def _extract_from_json(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from JSON file"""
        try:
            json_text = file_content.decode('utf-8')
            json_data = json.loads(json_text)
            
            # Convert JSON to readable text
            text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            return {
                "text": text_content,
                "metadata": {
                    "filename": filename,
                    "content_type": "application/json",
                    "extraction_method": "json",
                    "size": len(file_content)
                }
            }
        except Exception as e:
            logger.error(f"JSON extraction failed for {filename}: {e}")
            return {
                "text": "",
                "metadata": {
                    "filename": filename,
                    "content_type": "application/json",
                    "error": str(e),
                    "extraction_method": "json_failed"
                }
            }
    
    @staticmethod
    def _extract_from_text(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from plain text file"""
        try:
            text_content = file_content.decode('utf-8')
            
            return {
                "text": text_content,
                "metadata": {
                    "filename": filename,
                    "content_type": "text/plain",
                    "extraction_method": "text",
                    "size": len(file_content)
                }
            }
        except Exception as e:
            logger.error(f"Text extraction failed for {filename}: {e}")
            return {
                "text": "",
                "metadata": {
                    "filename": filename,
                    "content_type": "text/plain",
                    "error": str(e),
                    "extraction_method": "text_failed"
                }
            }
