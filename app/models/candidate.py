from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

class CandidateModel:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_candidate(self, candidate_data: dict) -> str:
        """Create a new candidate record"""
        candidate_doc = {
            **candidate_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "uploaded",
            "parsed_data": None,
            "resume_embeddings": None
        }
        result = await self.collection.insert_one(candidate_doc)
        return str(result.inserted_id)
    
    async def get_candidate(self, candidate_id: str) -> Optional[dict]:
        """Get candidate by ID"""
        try:
            obj_id = ObjectId(candidate_id)
            candidate = await self.collection.find_one({"_id": obj_id})
            if candidate:
                candidate["_id"] = str(candidate["_id"])
            return candidate
        except Exception:
            return None
    
    async def update_candidate(self, candidate_id: str, update_data: dict) -> bool:
        """Update candidate information"""
        try:
            obj_id = ObjectId(candidate_id)
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": obj_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def get_candidates_by_job(self, job_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all candidates for a specific job"""
        cursor = self.collection.find({"job_id": job_id}).skip(skip).limit(limit).sort("created_at", -1)
        candidates = await cursor.to_list(length=limit)
        for candidate in candidates:
            candidate["_id"] = str(candidate["_id"])
        return candidates
    
    async def update_parsed_data(self, candidate_id: str, parsed_data: dict) -> bool:
        """Update parsed resume data"""
        return await self.update_candidate(candidate_id, {
            "parsed_data": parsed_data,
            "status": "parsed"
        })
    
    async def update_embeddings(self, candidate_id: str, embeddings: List[float]) -> bool:
        """Update resume embeddings"""
        return await self.update_candidate(candidate_id, {
            "resume_embeddings": embeddings,
            "status": "embedded"
        })