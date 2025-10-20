from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

class InterviewSessionModel:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_session(self, session_data: dict) -> str:
        """Create a new interview session"""
        session_doc = {
            **session_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "current_question_index": 0,
            "questions_and_answers": [],
            "context": {},
            "is_completed": False
        }
        result = await self.collection.insert_one(session_doc)
        return str(result.inserted_id)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get interview session by ID"""
        try:
            obj_id = ObjectId(session_id)
            session = await self.collection.find_one({"_id": obj_id})
            if session:
                session["_id"] = str(session["_id"])
            return session
        except Exception:
            return None
    
    async def get_active_session(self, candidate_id: str, job_id: str) -> Optional[dict]:
        """Get active interview session for candidate and job"""
        session = await self.collection.find_one({
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": "active"
        })
        if session:
            session["_id"] = str(session["_id"])
        return session
    
    async def update_session(self, session_id: str, update_data: dict) -> bool:
        """Update interview session"""
        try:
            obj_id = ObjectId(session_id)
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": obj_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def add_question_answer(self, session_id: str, question: str, answer: str, 
                                question_score: Optional[float] = None, 
                                explanation: Optional[str] = None) -> bool:
        """Add a question-answer pair to the session"""
        try:
            obj_id = ObjectId(session_id)
            qa_pair = {
                "question": question,
                "answer": answer,
                "score": question_score,
                "explanation": explanation,
                "timestamp": datetime.utcnow()
            }
            
            result = await self.collection.update_one(
                {"_id": obj_id},
                {
                    "$push": {"questions_and_answers": qa_pair},
                    "$inc": {"current_question_index": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def update_context(self, session_id: str, context: dict) -> bool:
        """Update session context"""
        try:
            obj_id = ObjectId(session_id)
            result = await self.collection.update_one(
                {"_id": obj_id},
                {
                    "$set": {
                        "context": context,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def complete_session(self, session_id: str, overall_score: float, 
                             overall_assessment: str) -> bool:
        """Mark session as completed"""
        try:
            obj_id = ObjectId(session_id)
            result = await self.collection.update_one(
                {"_id": obj_id},
                {
                    "$set": {
                        "status": "completed",
                        "is_completed": True,
                        "overall_score": overall_score,
                        "overall_assessment": overall_assessment,
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def get_sessions_by_candidate(self, candidate_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all interview sessions for a candidate"""
        cursor = self.collection.find({"candidate_id": candidate_id}).skip(skip).limit(limit).sort("created_at", -1)
        sessions = await cursor.to_list(length=limit)
        for session in sessions:
            session["_id"] = str(session["_id"])
        return sessions
    
    async def get_sessions_by_job(self, job_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all interview sessions for a job"""
        cursor = self.collection.find({"job_id": job_id}).skip(skip).limit(limit).sort("created_at", -1)
        sessions = await cursor.to_list(length=limit)
        for session in sessions:
            session["_id"] = str(session["_id"])
        return sessions
