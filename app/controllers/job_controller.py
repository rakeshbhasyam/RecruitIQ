from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.schemas.job import JobCreate, JobResponse
from app.config.database import db

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate):
    """Create a new job posting"""
    try:
        job_id = await db.jobs.create_job(job_data.dict())
        job = await db.jobs.get_job(job_id)
        return job
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[JobResponse])
async def list_jobs(skip: int = 0, limit: int = 100):
    """List all jobs with pagination"""
    try:
        jobs = await db.jobs.list_jobs(skip=skip, limit=limit)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job by ID"""
    job = await db.jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job