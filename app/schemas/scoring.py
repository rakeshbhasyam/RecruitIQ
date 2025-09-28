from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

class ScoreBreakdown(BaseModel):
    skills_match: Optional[float] = Field(None, description="Skills matching score")
    exp_match: Optional[float] = Field(None, description="Experience matching score")
    interview: Optional[float] = Field(None, description="Interview score")
    additional_scores: Optional[Dict[str, float]] = Field(None, description="Additional scoring components")

class InterviewQuestion(BaseModel):
    question: str = Field(..., description="Interview question")
    answer: Optional[str] = Field(None, description="Candidate answer")
    score: Optional[float] = Field(None, description="Question score")
    explanation: Optional[str] = Field(None, description="Scoring explanation")
    rubric_criteria: Optional[Dict[str, Any]] = Field(None, description="Rubric criteria used")

class InterviewSession(BaseModel):
    questions: List[InterviewQuestion] = Field(..., description="Interview questions")
    overall_score: Optional[float] = Field(None, description="Overall interview score")
    duration_minutes: Optional[int] = Field(None, description="Interview duration")
    notes: Optional[str] = Field(None, description="Additional notes")

class ScoreCreate(BaseModel):
    candidate_id: str = Field(..., description="Candidate ID")
    job_id: str = Field(..., description="Job ID")

class ScoreResponse(ScoreCreate):
    id: str = Field(..., alias="_id", description="Score ID")
    matcher_score: Optional[float] = Field(None, description="Resume matching score")
    interview_score: Optional[float] = Field(None, description="Interview score")
    final_score: Optional[float] = Field(None, description="Final composite score")
    breakdown: Optional[ScoreBreakdown] = Field(None, description="Score breakdown")
    interview_session: Optional[InterviewSession] = Field(None, description="Interview session data")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }

class ScoreUpdate(BaseModel):
    matcher_score: Optional[float] = None
    interview_score: Optional[float] = None
    final_score: Optional[float] = None
    breakdown: Optional[ScoreBreakdown] = None
    interview_session: Optional[InterviewSession] = None