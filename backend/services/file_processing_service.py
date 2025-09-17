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
            logger.info(f"Starting text extraction from {filename} ({len(file_content)} bytes, {content_type})")
            
            # Get file extension
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            logger.info(f"File extension: {file_ext}")
            
            # Extract text based on file type
            if content_type == 'application/pdf' or file_ext == 'pdf':
                logger.info("Processing PDF file...")
                result = FileProcessingService._extract_from_pdf(file_content, filename)
            elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_ext == 'docx':
                logger.info("Processing DOCX file...")
                result = FileProcessingService._extract_from_docx(file_content, filename)
            elif content_type == 'text/csv' or file_ext == 'csv':
                logger.info("Processing CSV file...")
                result = FileProcessingService._extract_from_csv(file_content, filename)
            elif content_type == 'application/json' or file_ext == 'json':
                logger.info("Processing JSON file...")
                result = FileProcessingService._extract_from_json(file_content, filename)
            elif content_type.startswith('text/') or file_ext in ['txt', 'md']:
                logger.info("Processing text file...")
                result = FileProcessingService._extract_from_text(file_content, filename)
            else:
                logger.info("Processing unknown file type as text...")
                # Try to decode as text for unknown types
                result = FileProcessingService._extract_from_text(file_content, filename)
            
            logger.info(f"Text extraction completed: {len(result['text'])} characters extracted")
            return result
                
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
        """Extract text from CSV file with optimized processing for large files"""
        try:
            logger.info(f"Processing CSV file: {filename} ({len(file_content)} bytes)")
            
            csv_text = file_content.decode('utf-8')
            
            # For large files, use chunked processing
            if len(csv_text) > 10 * 1024 * 1024:  # 10MB 이상
                logger.info("Large CSV file detected, using chunked processing")
                return FileProcessingService._extract_from_csv_chunked(csv_text, filename, len(file_content))
            
            # For smaller files, use regular processing
            df = pd.read_csv(io.StringIO(csv_text))
            
            # Convert DataFrame to text with optimized formatting
            text_content = df.to_string(index=False, max_rows=10000)  # Limit rows for very large files
            
            # If file is too large, add truncation notice
            if len(df) > 10000:
                text_content += f"\n\n[파일이 너무 커서 처음 10,000행만 표시됩니다. 전체 행 수: {len(df)}]"
            
            return {
                "text": text_content,
                "metadata": {
                    "filename": filename,
                    "content_type": "text/csv",
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": list(df.columns),
                    "extraction_method": "csv",
                    "size": len(file_content),
                    "truncated": len(df) > 10000
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
    def _extract_from_csv_chunked(csv_text: str, filename: str, file_size: int) -> Dict[str, Any]:
        """Extract text from large CSV file using chunked processing"""
        try:
            logger.info("Starting chunked CSV processing")
            
            # Read CSV in chunks
            chunk_size = 1000
            chunks = []
            total_rows = 0
            columns = None
            
            # Use StringIO for chunked reading
            csv_io = io.StringIO(csv_text)
            
            for chunk_df in pd.read_csv(csv_io, chunksize=chunk_size):
                if columns is None:
                    columns = list(chunk_df.columns)
                
                total_rows += len(chunk_df)
                
                # Convert chunk to text
                chunk_text = chunk_df.to_string(index=False)
                chunks.append(chunk_text)
                
                # Limit total chunks to prevent memory issues
                if len(chunks) >= 50:  # Max 50,000 rows
                    logger.info(f"Reached chunk limit, processing {len(chunks) * chunk_size} rows")
                    break
            
            # Combine chunks
            text_content = "\n\n".join(chunks)
            
            # Add truncation notice if needed
            if total_rows >= 50000:
                text_content += f"\n\n[파일이 너무 커서 처음 50,000행만 표시됩니다. 전체 행 수: {total_rows}]"
            
            logger.info(f"Chunked CSV processing completed: {total_rows} rows processed")
            
            return {
                "text": text_content,
                "metadata": {
                    "filename": filename,
                    "content_type": "text/csv",
                    "row_count": total_rows,
                    "column_count": len(columns) if columns else 0,
                    "columns": columns or [],
                    "extraction_method": "csv_chunked",
                    "size": file_size,
                    "truncated": total_rows >= 50000
                }
            }
        except Exception as e:
            logger.error(f"Chunked CSV extraction failed for {filename}: {e}")
            # Fallback to basic text extraction
            return {
                "text": csv_text[:1000000],  # First 1MB as text
                "metadata": {
                    "filename": filename,
                    "content_type": "text/csv",
                    "extraction_method": "csv_fallback",
                    "size": file_size,
                    "note": "Large file processed as plain text"
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
