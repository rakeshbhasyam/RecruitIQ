from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.workflow_service import WorkflowService
from app.config.database import db
from app.schemas.interview_session import (
    InterviewSessionCreate, InterviewSessionResponse, 
    NextQuestionRequest, NextQuestionResponse
)

router = APIRouter(prefix="/interviews", tags=["interviews"])
workflow_service = WorkflowService()

class InterviewRequest(BaseModel):
    candidate_id: str
    job_id: str
    num_questions: int = 5

class InterviewAnswer(BaseModel):
    question: str
    answer: str

class InterviewSubmission(BaseModel):
    candidate_id: str
    job_id: str
    questions_and_answers: List[InterviewAnswer]

@router.post("/generate")
async def generate_interview_questions(request: InterviewRequest):
    """Generate interview questions for candidate"""
    try:
        result = await workflow_service.conduct_interview(
            request.candidate_id, 
            request.job_id, 
            request.num_questions
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/start")
async def start_interview_session(session_data: InterviewSessionCreate):
    """Start a new streaming interview session"""
    try:
        result = await workflow_service.start_interview_session(
            session_data.candidate_id,
            session_data.job_id,
            session_data.max_questions
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/next_question")
async def get_next_question(request: NextQuestionRequest):
    """Get the next question in the interview session"""
    try:
        result = await workflow_service.get_next_question(
            request.session_id,
            request.answer
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{session_id}")
async def get_interview_session(session_id: str):
    """Get interview session details"""
    try:
        session = await db.interview_sessions.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/candidate/{candidate_id}/sessions")
async def get_candidate_sessions(candidate_id: str, skip: int = 0, limit: int = 100):
    """Get all interview sessions for a candidate"""
    try:
        sessions = await db.interview_sessions.get_sessions_by_candidate(candidate_id, skip, limit)
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/job/{job_id}/sessions")
async def get_job_sessions(job_id: str, skip: int = 0, limit: int = 100):
    """Get all interview sessions for a job"""
    try:
        sessions = await db.interview_sessions.get_sessions_by_job(job_id, skip, limit)
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/submit")
async def submit_interview_answers(submission: InterviewSubmission):
    """Submit interview answers for evaluation (legacy endpoint)"""
    try:
        # Convert to expected format
        questions_and_answers = [
            {"question": qa.question, "answer": qa.answer} 
            for qa in submission.questions_and_answers
        ]
        
        result = await workflow_service.evaluate_interview(
            submission.candidate_id,
            submission.job_id,
            questions_and_answers
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))