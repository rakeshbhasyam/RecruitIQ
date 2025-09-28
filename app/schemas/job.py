from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

class JobCriteria(BaseModel):
    skills: List[str] = Field(..., description="Required skills for the job")
    exp_min: int = Field(..., description="Minimum years of experience")
    exp_max: int = Field(..., description="Maximum years of experience")
    weights: Dict[str, float] = Field(
        default={"skills": 0.5, "experience": 0.3, "interview": 0.2},
        description="Weights for different scoring components"
    )
    additional_criteria: Optional[Dict[str, Any]] = Field(None, description="Additional criteria")

class JobCreate(BaseModel):
    title: str = Field(..., description="Job title")
    jd_text: str = Field(..., description="Job description text")
    criteria: JobCriteria = Field(..., description="Job criteria")
    company: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Job location")

class JobResponse(JobCreate):
    id: str = Field(..., alias="_id", description="Job ID")
    jd_embeddings: Optional[List[float]] = Field(None, description="Job description embeddings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    status: str = Field(default="active", description="Job status")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }