import asyncio
from typing import Dict, Any, Optional
from app.agents import (
    ResumeIngestionAgent,
    ResumeParserAgent,
    ResumeMatcherAgent,
    InterviewAgent,
    FinalScoringAgent
)
from app.config.database import db
import uuid

class WorkflowService:
    def __init__(self):
        self.ingestion_agent = ResumeIngestionAgent()
        self.parser_agent = ResumeParserAgent()
        self.matcher_agent = ResumeMatcherAgent()
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
            
            job_id = candidate["job_id"]
            
            # Step 1: Ingestion - Extract text from resume
            ingestion_result = await self.ingestion_agent.process_resume(candidate_id, file_path, trace_id)
            extracted_text = ingestion_result["extracted_text"]
            
            # Step 2: Parsing - Extract structured data
            parsed_data = await self.parser_agent.parse_resume(candidate_id, extracted_text, trace_id)
            
            # Step 3: Matching - Score against job requirements
            matching_result = await self.matcher_agent.match_candidate(candidate_id, job_id, trace_id)
            
            # Step 4: Calculate final score (interview will be done separately)
            final_result = await self.scoring_agent.calculate_final_score(candidate_id, job_id, trace_id)
            
            return {
                "trace_id": trace_id,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "ingestion": ingestion_result,
                "parsing": parsed_data,
                "matching": matching_result,
                "final_scoring": final_result
            }
            
        except Exception as e:
            # Log the error
            await db.audit_logs.create_log({
                "trace_id": trace_id,
                "agent": "WorkflowService",
                "error": str(e),
                "candidate_id": candidate_id
            })
            raise e
    
    async def conduct_interview(self, candidate_id: str, job_id: str, num_questions: int = 5) -> Dict[str, Any]:
        """Generate interview questions for candidate"""
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