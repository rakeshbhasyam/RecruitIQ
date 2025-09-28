from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from typing import List, Optional
from app.schemas.candidate import CandidateCreate, CandidateResponse
from app.config.database import db
from app.services.workflow_service import WorkflowService
import tempfile
import os

router = APIRouter(prefix="/candidates", tags=["candidates"])
workflow_service = WorkflowService()

@router.post("/upload", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(job_id: str = Form(...), email: Optional[str] = Form(None), resume: UploadFile = File(...)):
    """Upload candidate resume and start processing"""
    try:
        # Validate file type
        if not resume.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or Word document.")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume.filename)[1]) as tmp_file:
            content = await resume.read()
            tmp_file.write(content)
            file_path = tmp_file.name
        
        # Create candidate record
        candidate_data = CandidateCreate(job_id=job_id, resume_uri=file_path, email=email)
        candidate_id = await db.candidates.create_candidate(candidate_data.dict())
        
        # Create score record
        await db.scores.create_score({"candidate_id": candidate_id, "job_id": job_id})
        
        # Start async processing workflow
        await workflow_service.process_candidate(candidate_id, file_path)
        
        # Get and return candidate
        candidate = await db.candidates.get_candidate(candidate_id)
        return candidate
        
    except Exception as e:
        # Clean up temp file on error
        if 'file_path' in locals():
            try:
                os.unlink(file_path)
            except:
                pass
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/job/{job_id}", response_model=List[CandidateResponse])
async def get_candidates_by_job(job_id: str, skip: int = 0, limit: int = 100):
    """Get all candidates for a specific job"""
    try:
        candidates = await db.candidates.get_candidates_by_job(job_id, skip=skip, limit=limit)
        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    """Get candidate by ID"""
    candidate = await db.candidates.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate