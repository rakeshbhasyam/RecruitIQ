from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

# In-memory mock database for when MongoDB is not available

class MockJobModel:
    def __init__(self):
        self.jobs = {}
    
    async def create_job(self, job_data: dict) -> str:
        job_id = str(uuid.uuid4())
        job_doc = {
            **job_data,
            "_id": job_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "jd_embeddings": None
        }
        self.jobs[job_id] = job_doc
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[dict]:
        job = self.jobs.get(job_id)
        if job:
            job["_id"] = str(job["_id"])
        return job
    
    async def update_job(self, job_id: str, update_data: dict) -> bool:
        if job_id in self.jobs:
            self.jobs[job_id].update(update_data)
            self.jobs[job_id]["updated_at"] = datetime.utcnow()
            return True
        return False
    
    async def list_jobs(self, skip: int = 0, limit: int = 100) -> List[dict]:
        jobs = list(self.jobs.values())[skip:skip+limit]
        for job in jobs:
            job["_id"] = str(job["_id"])
        return jobs
    
    async def update_embeddings(self, job_id: str, embeddings: List[float]) -> bool:
        return await self.update_job(job_id, {"jd_embeddings": embeddings})

class MockCandidateModel:
    def __init__(self):
        self.candidates = {}
    
    async def create_candidate(self, candidate_data: dict) -> str:
        candidate_id = str(uuid.uuid4())
        candidate_doc = {
            **candidate_data,
            "_id": candidate_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "uploaded",
            "parsed_data": None,
            "resume_embeddings": None
        }
        self.candidates[candidate_id] = candidate_doc
        return candidate_id
    
    async def get_candidate(self, candidate_id: str) -> Optional[dict]:
        candidate = self.candidates.get(candidate_id)
        if candidate:
            candidate["_id"] = str(candidate["_id"])
        return candidate
    
    async def update_candidate(self, candidate_id: str, update_data: dict) -> bool:
        if candidate_id in self.candidates:
            self.candidates[candidate_id].update(update_data)
            self.candidates[candidate_id]["updated_at"] = datetime.utcnow()
            return True
        return False
    
    async def get_candidates_by_job(self, job_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        candidates = [c for c in self.candidates.values() if c.get("job_id") == job_id][skip:skip+limit]
        for candidate in candidates:
            candidate["_id"] = str(candidate["_id"])
        return candidates
    
    async def update_parsed_data(self, candidate_id: str, parsed_data: dict) -> bool:
        return await self.update_candidate(candidate_id, {"parsed_data": parsed_data, "status": "parsed"})
    
    async def update_embeddings(self, candidate_id: str, embeddings: List[float]) -> bool:
        return await self.update_candidate(candidate_id, {"resume_embeddings": embeddings, "status": "embedded"})

class MockScoreModel:
    def __init__(self):
        self.scores = {}
    
    async def create_score(self, score_data: dict) -> str:
        score_id = str(uuid.uuid4())
        score_doc = {
            **score_data,
            "_id": score_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "matcher_score": None,
            "interview_score": None,
            "final_score": None,
            "breakdown": None,
            "interview_session": None
        }
        self.scores[score_id] = score_doc
        return score_id
    
    async def get_score(self, score_id: str) -> Optional[dict]:
        score = self.scores.get(score_id)
        if score:
            score["_id"] = str(score["_id"])
        return score
    
    async def get_score_by_candidate(self, candidate_id: str) -> Optional[dict]:
        for score in self.scores.values():
            if score.get("candidate_id") == candidate_id:
                score["_id"] = str(score["_id"])
                return score
        return None
    
    async def update_score(self, score_id: str, update_data: dict) -> bool:
        if score_id in self.scores:
            self.scores[score_id].update(update_data)
            self.scores[score_id]["updated_at"] = datetime.utcnow()
            return True
        return False
    
    async def update_matcher_score(self, candidate_id: str, matcher_score: float, breakdown: dict) -> bool:
        for score in self.scores.values():
            if score.get("candidate_id") == candidate_id:
                score.update({
                    "matcher_score": matcher_score,
                    "breakdown": breakdown,
                    "updated_at": datetime.utcnow()
                })
                return True
        return False
    
    async def update_interview_score(self, candidate_id: str, interview_session: dict) -> bool:
        for score in self.scores.values():
            if score.get("candidate_id") == candidate_id:
                score.update({
                    "interview_score": interview_session.get("overall_score"),
                    "interview_session": interview_session,
                    "updated_at": datetime.utcnow()
                })
                return True
        return False
    
    async def update_final_score(self, candidate_id: str, final_score: float) -> bool:
        for score in self.scores.values():
            if score.get("candidate_id") == candidate_id:
                score.update({
                    "final_score": final_score,
                    "updated_at": datetime.utcnow()
                })
                return True
        return False
    
    async def get_scores_by_job(self, job_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        scores = [s for s in self.scores.values() if s.get("job_id") == job_id][skip:skip+limit]
        scores.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        for score in scores:
            score["_id"] = str(score["_id"])
        return scores

class MockAuditModel:
    def __init__(self):
        self.logs = {}
    
    async def create_log(self, log_data: dict) -> str:
        log_id = str(uuid.uuid4())
        log_doc = {
            **log_data,
            "_id": log_id,
            "timestamp": datetime.utcnow()
        }
        self.logs[log_id] = log_doc
        return log_id
    
    async def get_logs_by_trace(self, trace_id: str) -> List[dict]:
        logs = [log for log in self.logs.values() if log.get("trace_id") == trace_id]
        logs.sort(key=lambda x: x.get("timestamp"))
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
    
    async def get_logs_by_job(self, job_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        logs = [log for log in self.logs.values() if log.get("job_id") == job_id][skip:skip+limit]
        logs.sort(key=lambda x: x.get("timestamp"), reverse=True)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
    
    async def get_logs_by_candidate(self, candidate_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        logs = [log for log in self.logs.values() if log.get("candidate_id") == candidate_id][skip:skip+limit]
        logs.sort(key=lambda x: x.get("timestamp"), reverse=True)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
    
    async def get_logs_by_agent(self, agent: str, skip: int = 0, limit: int = 100) -> List[dict]:
        logs = [log for log in self.logs.values() if log.get("agent") == agent][skip:skip+limit]
        logs.sort(key=lambda x: x.get("timestamp"), reverse=True)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs