from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.config.database import db

class FinalScoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("FinalScoringAgent")
    
    async def calculate_final_score(self, candidate_id: str, job_id: str, trace_id: str) -> Dict[str, Any]:
        """Calculate final composite score for candidate"""
        try:
            # Get score record and job criteria
            score_record = await db.scores.get_score_by_candidate(candidate_id)
            job = await db.jobs.get_job(job_id)
            
            if not score_record or not job:
                raise ValueError("Score record or job not found")
            
            # Get criteria weights
            criteria = job.get("criteria", {})
            weights = criteria.get("weights", {"skills": 0.5, "experience": 0.3, "interview": 0.2})
            
            # Get individual scores
            matcher_score = score_record.get("matcher_score", 0.0) or 0.0
            interview_score = score_record.get("interview_score", 0.0) or 0.0
            
            # Calculate weighted final score
            final_score = (
                matcher_score * weights.get("skills", 0.5) +
                matcher_score * weights.get("experience", 0.0) +  # Experience is part of matcher score
                interview_score * weights.get("interview", 0.2)
            )
            
            # Ensure score is between 0 and 1
            final_score = min(1.0, max(0.0, final_score))
            
            # Update final score in database
            await db.scores.update_final_score(candidate_id, final_score)
            
            result = {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "matcher_score": matcher_score,
                "interview_score": interview_score,
                "final_score": final_score,
                "weights_used": weights
            }
            
            # Log the calculation
            await self.log_activity(
                trace_id=trace_id,
                prompt=f"Calculating final score for candidate {candidate_id}",
                response=f"Final score: {final_score}",
                metadata=result,
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            return result
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id,
                job_id=job_id
            )
            raise e