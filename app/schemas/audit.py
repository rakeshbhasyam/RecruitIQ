from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

class AuditLogCreate(BaseModel):
    trace_id: str = Field(..., description="Unique trace identifier")
    agent: str = Field(..., description="Agent name that generated the log")
    prompt: Optional[str] = Field(None, description="Input prompt to the agent")
    response: Optional[Any] = Field(None, description="Agent response")
    tools_used: Optional[List[str]] = Field(None, description="Tools used by the agent")
    error: Optional[str] = Field(None, description="Error message if any")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    job_id: Optional[str] = Field(None, description="Associated job ID")
    candidate_id: Optional[str] = Field(None, description="Associated candidate ID")

class AuditLogResponse(AuditLogCreate):
    id: str = Field(..., alias="_id", description="Audit log ID")
    timestamp: datetime = Field(..., description="Log timestamp")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }