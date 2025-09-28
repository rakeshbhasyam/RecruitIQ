from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

class ParsedData(BaseModel):
    name: Optional[str] = Field(None, description="Candidate name")
    skills: List[str] = Field(default=[], description="Extracted skills")
    experience: int = Field(default=0, description="Years of experience")
    education: Optional[str] = Field(None, description="Education details")
    job_titles: List[str] = Field(default=[], description="Previous job titles")
    certifications: List[str] = Field(default=[], description="Certifications")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Contact information")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional parsed information")

class CandidateCreate(BaseModel):
    job_id: str = Field(..., description="Associated job ID")
    resume_uri: Optional[str] = Field(None, description="Resume file URI")
    email: Optional[str] = Field(None, description="Candidate email")

class CandidateResponse(CandidateCreate):
    id: str = Field(..., alias="_id", description="Candidate ID")
    parsed_data: Optional[ParsedData] = Field(None, description="Parsed resume data")
    resume_embeddings: Optional[List[float]] = Field(None, description="Resume embeddings")
    status: str = Field(default="uploaded", description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }

class CandidateUpdate(BaseModel):
    parsed_data: Optional[ParsedData] = None
    resume_embeddings: Optional[List[float]] = None
    status: Optional[str] = None