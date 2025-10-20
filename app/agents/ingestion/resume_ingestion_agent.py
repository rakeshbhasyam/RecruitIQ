"""
Resume Ingestion Agent for RecruitIQ system.
Handles text extraction from various resume file formats.
"""

import aiofiles
import PyPDF2
from docx import Document
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.config.database import db

class ResumeIngestionAgent(BaseAgent):
    """
    AI agent responsible for extracting text from resume files.
    
    Supported formats:
    - PDF files using PyPDF2
    - DOCX files using python-docx
    """
    
    def __init__(self):
        super().__init__("ResumeIngestionAgent")
    
    async def process_resume(self, candidate_id: str, file_path: str, trace_id: str) -> Dict[str, Any]:
        """
        Extract text from resume file based on file format.
        
        Args:
            candidate_id: Unique identifier for the candidate
            file_path: Path to the resume file
            trace_id: Unique identifier for tracking this operation
            
        Returns:
            Dictionary containing extracted text and metadata
            
        Raises:
            ValueError: If file format is not supported
            Exception: If text extraction fails
        """
        try:
            await self.log_activity(
                trace_id=trace_id,
                prompt=f"Processing resume file: {file_path}",
                tools_used=["file_reader"],
                candidate_id=candidate_id
            )
            
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                extracted_text = await self._extract_pdf_text(file_path)
            elif file_extension in ['doc', 'docx']:
                extracted_text = await self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            await db.candidates.update_candidate(candidate_id, {
                "status": "ingested"
            })
            
            result = {
                "extracted_text": extracted_text,
                "file_type": file_extension,
                "text_length": len(extracted_text)
            }
            
            await self.log_activity(
                trace_id=trace_id,
                response=f"Successfully extracted {len(extracted_text)} characters",
                metadata=result,
                candidate_id=candidate_id
            )
            
            return result
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id
            )
            raise e
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """
        Extract text from PDF file using PyPDF2.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        async with aiofiles.open(file_path, 'rb') as file:
            content = await file.read()
            
        from io import BytesIO
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """
        Extract text from DOCX file using python-docx.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Extracted text content
        """
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()