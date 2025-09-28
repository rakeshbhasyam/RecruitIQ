from .job_controller import router as job_router
from .candidate_controller import router as candidate_router
from .interview_controller import router as interview_router
from .scoring_controller import router as scoring_router

__all__ = [
    "job_router",
    "candidate_router",
    "interview_router",
    "scoring_router"
]