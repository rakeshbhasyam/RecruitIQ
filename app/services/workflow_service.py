import asyncio
from typing import Dict, Any, Optional
import uuid

from app.config.database import db
from app.agents import InterviewAgent, FinalScoringAgent
from app.services.graph_service import recruitment_graph, AgentState

class WorkflowService:
    def __init__(self):
        self.interview_agent = InterviewAgent()
        self.scoring_agent = FinalScoringAgent()
    
    async def process_candidate(self, candidate_id: str, file_path: str) -> Dict[str, Any]:
        """Process candidate through the full pipeline"""
        trace_id = str(uuid.uuid4())
        
        try:
            # Get candidate to get job_id
            candidate = await db.candidates.get_candidate(candidate_id)
            if not candidate:
                raise ValueError("Candidate not found")
            
            initial_state: AgentState = {
                "trace_id": trace_id,
                "candidate_id": candidate_id,
                "job_id": candidate["job_id"],
                "file_path": file_path,
                "resume_text": None,
                "candidate_profile": None,
                "job_match_report": None,
                "interview_criteria": None,
                "final_score": None,
                "final_report": None,
            }
            
            # Invoke the graph asynchronously
            final_state = await recruitment_graph.ainvoke(initial_state)
            return final_state.get("final_report", {})
            
        except Exception as e:
            # Log the error
            await db.audit_logs.create_log({
                "trace_id": trace_id,
                "agent": "WorkflowService",
                "error": str(e),
                "candidate_id": candidate_id
            })
            raise e
    
    async def start_interview_session(self, candidate_id: str, job_id: str, max_questions: int = 5) -> Dict[str, Any]:
        """Start a new streaming interview session"""
        trace_id = str(uuid.uuid4())
        
        try:
            result = await self.interview_agent.start_interview_session(
                candidate_id, job_id, max_questions, trace_id
            )
            
            return {
                "trace_id": trace_id,
                **result
            }
            
        except Exception as e:
            await db.audit_logs.create_log({
                "trace_id": trace_id,
                "agent": "WorkflowService",
                "error": str(e),
                "candidate_id": candidate_id,
                "job_id": job_id
            })
            raise e
    
    async def get_next_question(self, session_id: str, answer: Optional[str] = None) -> Dict[str, Any]:
        """Get the next question in the interview session"""
        trace_id = str(uuid.uuid4())
        
        try:
            result = await self.interview_agent.get_next_question(session_id, answer, trace_id)
            
            return {
                "trace_id": trace_id,
                **result
            }
            
        except Exception as e:
            await db.audit_logs.create_log({
                "trace_id": trace_id,
                "agent": "WorkflowService",
                "error": str(e),
                "session_id": session_id
            })
            raise e

    async def conduct_interview(self, candidate_id: str, job_id: str, num_questions: int = 5) -> Dict[str, Any]:
        """Generate interview questions for candidate (legacy method)"""
        trace_id = str(uuid.uuid4())
        
        try:
            questions = await self.interview_agent.generate_questions(candidate_id, job_id, trace_id, num_questions)
            
            return {
                "trace_id": trace_id,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "questions": questions
            }
            
        except Exception as e:
            await db.audit_logs.create_log({
                "trace_id": trace_id,
                "agent": "WorkflowService",
                "error": str(e),
                "candidate_id": candidate_id,
                "job_id": job_id
            })
            raise e
    
    async def evaluate_interview(self, candidate_id: str, job_id: str, questions_and_answers: list) -> Dict[str, Any]:
        """Evaluate interview answers and update final score"""
        trace_id = str(uuid.uuid4())
        
        try:
            # Evaluate interview
            interview_session = await self.interview_agent.evaluate_answers(
                candidate_id, job_id, questions_and_answers, trace_id
            )
            
            # Recalculate final score with interview included
            final_result = await self.scoring_agent.calculate_final_score(candidate_id, job_id, trace_id)
            
            return {
                "trace_id": trace_id,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "interview_session": interview_session,
                "final_scoring": final_result
            }
            
        except Exception as e:
            await db.audit_logs.create_log({
                "trace_id": trace_id,
                "agent": "WorkflowService",
                "error": str(e),
                "candidate_id": candidate_id,
                "job_id": job_id
            })
            raise e