from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel
from app.services.workflow_service import WorkflowService
from app.config.database import db

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

@router.post("/submit")
async def submit_interview_answers(submission: InterviewSubmission):
    """Submit interview answers for evaluation"""
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