from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

class ScoreModel:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_score(self, score_data: dict) -> str:
        """Create a new score record"""
        score_doc = {
            **score_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "matcher_score": None,
            "interview_score": None,
            "final_score": None,
            "breakdown": None,
            "interview_session": None
        }
        result = await self.collection.insert_one(score_doc)
        return str(result.inserted_id)
    
    async def get_score(self, score_id: str) -> Optional[dict]:
        """Get score by ID"""
        try:
            obj_id = ObjectId(score_id)
            score = await self.collection.find_one({"_id": obj_id})
            if score:
                score["_id"] = str(score["_id"])
            return score
        except Exception:
            return None
    
    async def get_score_by_candidate(self, candidate_id: str) -> Optional[dict]:
        """Get score by candidate ID"""
        score = await self.collection.find_one({"candidate_id": candidate_id})
        if score:
            score["_id"] = str(score["_id"])
        return score
    
    async def update_score(self, score_id: str, update_data: dict) -> bool:
        """Update score information"""
        try:
            obj_id = ObjectId(score_id)
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": obj_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def update_matcher_score(self, candidate_id: str, matcher_score: float, breakdown: dict) -> bool:
        """Update matcher score and breakdown"""
        result = await self.collection.update_one(
            {"candidate_id": candidate_id},
            {"$set": {
                "matcher_score": matcher_score,
                "breakdown": breakdown,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    async def update_interview_score(self, candidate_id: str, interview_session: dict) -> bool:
        """Update interview score and session data"""
        result = await self.collection.update_one(
            {"candidate_id": candidate_id},
            {"$set": {
                "interview_score": interview_session.get("overall_score"),
                "interview_session": interview_session,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    async def update_final_score(self, candidate_id: str, final_score: float) -> bool:
        """Update final composite score"""
        result = await self.collection.update_one(
            {"candidate_id": candidate_id},
            {"$set": {
                "final_score": final_score,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    async def get_scores_by_job(self, job_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all scores for a specific job"""
        cursor = self.collection.find({"job_id": job_id}).skip(skip).limit(limit).sort("final_score", -1)
        scores = await cursor.to_list(length=limit)
        for score in scores:
            score["_id"] = str(score["_id"])
        return scores