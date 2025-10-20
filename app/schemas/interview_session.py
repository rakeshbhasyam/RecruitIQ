from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

class QuestionAnswerPair(BaseModel):
    question: str = Field(..., description="Interview question")
    answer: str = Field(..., description="Candidate answer")
    score: Optional[float] = Field(None, description="Question score (0.0-1.0)")
    explanation: Optional[str] = Field(None, description="Scoring explanation")
    timestamp: datetime = Field(..., description="When the answer was submitted")

class InterviewSessionCreate(BaseModel):
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")
    max_questions: int = Field(default=5, description="Maximum number of questions")
    interview_type: str = Field(default="technical", description="Type of interview")

class InterviewSessionResponse(InterviewSessionCreate):
    id: str = Field(..., alias="_id", description="Session ID")
    status: str = Field(default="active", description="Session status")
    current_question_index: int = Field(default=0, description="Current question number")
    questions_and_answers: List[QuestionAnswerPair] = Field(default=[], description="Q&A pairs")
    context: Dict[str, Any] = Field(default={}, description="Session context")
    is_completed: bool = Field(default=False, description="Whether session is completed")
    overall_score: Optional[float] = Field(None, description="Overall interview score")
    overall_assessment: Optional[str] = Field(None, description="Overall assessment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }

class NextQuestionRequest(BaseModel):
    session_id: str = Field(..., description="Interview session ID")
    answer: Optional[str] = Field(None, description="Answer to previous question (if any)")

class NextQuestionResponse(BaseModel):
    session_id: str = Field(..., description="Interview session ID")
    question: Optional[str] = Field(None, description="Next question (None if interview is complete)")
    question_index: int = Field(..., description="Current question index")
    is_complete: bool = Field(..., description="Whether interview is complete")
    context: Dict[str, Any] = Field(default={}, description="Updated session context")
    previous_qa: Optional[QuestionAnswerPair] = Field(None, description="Previous Q&A pair if just answered")

class InterviewSessionUpdate(BaseModel):
    status: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    is_completed: Optional[bool] = None
    overall_score: Optional[float] = None
    overall_assessment: Optional[str] = None
