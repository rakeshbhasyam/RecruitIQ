from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

class AuditModel:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_log(self, log_data: dict) -> str:
        """Create a new audit log entry"""
        log_doc = {
            **log_data,
            "timestamp": datetime.utcnow()
        }
        result = await self.collection.insert_one(log_doc)
        return str(result.inserted_id)
    
    async def get_logs_by_trace(self, trace_id: str) -> List[dict]:
        """Get all logs for a specific trace ID"""
        cursor = self.collection.find({"trace_id": trace_id}).sort("timestamp", 1)
        logs = await cursor.to_list(length=None)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
    
    async def get_logs_by_job(self, job_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get logs for a specific job"""
        cursor = self.collection.find({"job_id": job_id}).skip(skip).limit(limit).sort("timestamp", -1)
        logs = await cursor.to_list(length=limit)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
    
    async def get_logs_by_candidate(self, candidate_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get logs for a specific candidate"""
        cursor = self.collection.find({"candidate_id": candidate_id}).skip(skip).limit(limit).sort("timestamp", -1)
        logs = await cursor.to_list(length=limit)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
    
    async def get_logs_by_agent(self, agent: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get logs for a specific agent"""
        cursor = self.collection.find({"agent": agent}).skip(skip).limit(limit).sort("timestamp", -1)
        logs = await cursor.to_list(length=limit)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs