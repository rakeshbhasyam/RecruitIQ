from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

class JobModel:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_job(self, job_data: dict) -> str:
        """Create a new job posting"""
        job_doc = {
            **job_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "jd_embeddings": None  # Will be updated by embedding agent
        }
        result = await self.collection.insert_one(job_doc)
        return str(result.inserted_id)
    
    async def get_job(self, job_id: str) -> Optional[dict]:
        """Get job by ID"""
        try:
            obj_id = ObjectId(job_id)
            job = await self.collection.find_one({"_id": obj_id})
            if job:
                job["_id"] = str(job["_id"])
            return job
        except Exception:
            return None
    
    async def update_job(self, job_id: str, update_data: dict) -> bool:
        """Update job information"""
        try:
            obj_id = ObjectId(job_id)
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": obj_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def list_jobs(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """List all jobs with pagination"""
        cursor = self.collection.find({}).skip(skip).limit(limit).sort("created_at", -1)
        jobs = await cursor.to_list(length=limit)
        for job in jobs:
            job["_id"] = str(job["_id"])
        return jobs
    
    async def update_embeddings(self, job_id: str, embeddings: List[float]) -> bool:
        """Update job description embeddings"""
        return await self.update_job(job_id, {"jd_embeddings": embeddings})