from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any
from datetime import datetime
from bson import ObjectId

class ContactInfo(BaseModel):
    """Schema for structured candidate contact information."""
    name: Optional[str] = Field(None, description="Candidate's full name")
    email: Optional[EmailStr] = Field(None, description="Candidate's email address")
    phone: Optional[str] = Field(None, description="Candidate's phone number")
    location: Optional[str] = Field(None, description="Candidate's location (city, state, etc.)")
    linkedin: Optional[str] = Field(None, description="URL to LinkedIn profile")
    github: Optional[str] = Field(None, description="URL to GitHub profile")

class ParsedData(BaseModel):
    name: Optional[str] = Field(None, description="Candidate name")
    skills: List[str] = Field(default=[], description="Extracted skills")
    experience_years: Optional[float] = Field(None, description="Total years of professional experience")
    education: Optional[str] = Field(None, description="Education details")
    job_titles: List[str] = Field(default=[], description="Previous job titles")
    projects: List[str] = Field(default=[], description="Key projects mentioned")
    summary: Optional[str] = Field(None, description="AI-generated summary of the candidate's profile")
    certifications: List[str] = Field(default=[], description="Certifications")
    contact_info: Optional[ContactInfo] = Field(None, description="Structured contact information")
    additional_info: Optional[dict[str, Any]] = Field(None, description="Additional parsed information")

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