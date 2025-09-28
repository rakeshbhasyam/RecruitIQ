import aiofiles
import PyPDF2
from docx import Document
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.config.database import db

class ResumeIngestionAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResumeIngestionAgent")
    
    async def process_resume(self, candidate_id: str, file_path: str, trace_id: str) -> Dict[str, Any]:
        """Extract text from resume file"""
        try:
            # Log the start of processing
            await self.log_activity(
                trace_id=trace_id,
                prompt=f"Processing resume file: {file_path}",
                tools_used=["file_reader"],
                candidate_id=candidate_id
            )
            
            extracted_text = ""
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                extracted_text = await self._extract_pdf_text(file_path)
            elif file_extension in ['doc', 'docx']:
                extracted_text = await self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            # Update candidate status
            await db.candidates.update_candidate(candidate_id, {
                "status": "ingested"
            })
            
            result = {
                "extracted_text": extracted_text,
                "file_type": file_extension,
                "text_length": len(extracted_text)
            }
            
            # Log successful completion
            await self.log_activity(
                trace_id=trace_id,
                response=f"Successfully extracted {len(extracted_text)} characters",
                metadata=result,
                candidate_id=candidate_id
            )
            
            return result
            
        except Exception as e:
            # Log error
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id
            )
            raise e
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        async with aiofiles.open(file_path, 'rb') as file:
            content = await file.read()
            
        # Use PyPDF2 to extract text
        from io import BytesIO
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()