from fastapi import APIRouter, HTTPException, status
from typing import List
from app.schemas.scoring import ScoreResponse
from app.config.database import db

router = APIRouter(prefix="/scores", tags=["scores"])

@router.get("/candidate/{candidate_id}", response_model=ScoreResponse)
async def get_candidate_score(candidate_id: str):
    """Get score for a specific candidate"""
    score = await db.scores.get_score_by_candidate(candidate_id)
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    return score

@router.get("/job/{job_id}", response_model=List[ScoreResponse])
async def get_job_scores(job_id: str, skip: int = 0, limit: int = 100):
    """Get all scores for a specific job (leaderboard)"""
    try:
        scores = await db.scores.get_scores_by_job(job_id, skip=skip, limit=limit)
        return scores
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))