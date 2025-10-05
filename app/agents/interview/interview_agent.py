import json
from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent
from app.config.database import db

class InterviewAgent(BaseAgent):
    def __init__(self):
        super().__init__("InterviewAgent")
    
    async def generate_questions(
        self, 
        candidate_id: str, 
        job_id: str, 
        trace_id: str, 
        num_questions: int = 3,
        generate_criteria: bool = False
    ) -> List[Any]:
        try:
            # Get candidate and job data
            candidate = await db.candidates.get_candidate(candidate_id)
            job = await db.jobs.get_job(job_id)
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Create question generation prompt
            if generate_criteria:
                prompt = self._create_interview_criteria_prompt(candidate, job, num_questions)
            else:
                prompt = self._create_question_prompt(candidate, job, num_questions)
            
            # Log the request
            await self.log_activity(
                trace_id=trace_id,
                prompt=prompt[:500] + "...",
                tools_used=["gemini"],
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            # Call Gemini to generate questions
            response = await self.call_gemini(prompt, max_tokens=1500)
            
            # Extract questions from response
            if generate_criteria:
                questions = self._extract_json_response(response)
            else:
                questions = self._extract_questions(response)
            
            # Log successful completion
            await self.log_activity(
                trace_id=trace_id,
                response=json.dumps(questions, indent=2),
                metadata={"question_count": len(questions)},
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            return questions
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id,
                job_id=job_id
            )
            raise e
    
    async def evaluate_answers(self, candidate_id: str, job_id: str, 
                             questions_and_answers: List[Dict[str, str]], trace_id: str) -> Dict[str, Any]:
        """Evaluate candidate answers and generate scores"""
        try:
            # Get job data for context
            job = await db.jobs.get_job(job_id)
            if not job:
                raise ValueError("Job not found")
            
            # Create evaluation prompt
            prompt = self._create_evaluation_prompt(job, questions_and_answers)
            
            # Log the evaluation request
            await self.log_activity(
                trace_id=trace_id,
                prompt=prompt[:500] + "...",
                tools_used=["gemini"],
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            # Call Gemini to evaluate answers
            response = await self.call_gemini(prompt, max_tokens=2000)
            
            # Extract evaluation results
            evaluation = self._extract_evaluation(response)
            
            # Create interview session data
            interview_session = {
                "questions": [
                    {
                        "question": qa["question"],
                        "answer": qa["answer"],
                        "score": evaluation.get("question_scores", [])[i] if i < len(evaluation.get("question_scores", [])) else 0.5,
                        "explanation": evaluation.get("question_explanations", [])[i] if i < len(evaluation.get("question_explanations", [])) else "No explanation available"
                    }
                    for i, qa in enumerate(questions_and_answers)
                ],
                "overall_score": evaluation.get("overall_score", 0.5),
                "duration_minutes": None,
                "notes": evaluation.get("overall_assessment", "")
            }
            
            # Update score in database
            await db.scores.update_interview_score(candidate_id, interview_session)
            
            # Log successful completion
            await self.log_activity(
                trace_id=trace_id,
                response=json.dumps(interview_session, indent=2),
                metadata={"overall_score": interview_session["overall_score"]},
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            return interview_session
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id,
                job_id=job_id
            )
            raise e
    
    def _create_question_prompt(self, candidate: Dict[str, Any], job: Dict[str, Any], num_questions: int) -> str:
        """Create prompt for generating interview questions"""
        candidate_data = candidate.get("parsed_data", {})
        
        return f"""You are an expert technical interviewer. Generate {num_questions} interview questions tailored to this specific candidate and job.

Job Details:
- Title: {job.get('title', 'N/A')}
- Required Skills: {', '.join(job.get('criteria', {}).get('skills', []))}
- Experience Level: {job.get('criteria', {}).get('exp_min', 0)}-{job.get('criteria', {}).get('exp_max', 10)} years
- Job Description: {job.get('jd_text', '')[:500]}...

Candidate Profile:
- Skills: {', '.join(candidate_data.get('skills', []))}
- Experience: {candidate_data.get('experience', 0)} years
- Previous Roles: {', '.join(candidate_data.get('job_titles', []))}

Generate questions that:
1. Test technical skills relevant to the job
2. Assess experience level and problem-solving
3. Are appropriate for the candidate's background
4. Mix of technical, behavioral, and scenario-based questions
5. Progressive difficulty based on the role level

Return the questions as a JSON array of strings:
["Question 1", "Question 2", "Question 3", ...]

JSON Response:"""
    
    def _create_interview_criteria_prompt(self, candidate: Dict[str, Any], job: Dict[str, Any], num_questions: int) -> str:
        """Create prompt for generating interview criteria and questions."""
        candidate_data = candidate.get("parsed_data", {})
        
        return f"""You are an expert HR strategist. Based on the job description and candidate profile, create an interview scoring rubric.

Job Details:
- Title: {job.get('title', 'N/A')}
- Required Skills: {', '.join(job.get('criteria', {}).get('skills', []))}

Candidate Profile:
- Skills: {', '.join(candidate_data.get('skills', []))}
- Experience: {candidate_data.get('experience_years', 0)} years

Generate a JSON array of criteria objects. Each object should contain:
1. "name": The evaluation criterion (e.g., "Technical Depth").
2. "description": What is being assessed.
3. "scoring_logic": How to rate the candidate on a 1-5 scale.
4. "sample_questions": An array of {num_questions} relevant questions for that criterion.

Example format:
[
  {{"name": "Technical Depth", "description": "...", "scoring_logic": "...", "sample_questions": ["..."]}}
]

JSON Response:"""
    
    def _create_evaluation_prompt(self, job: Dict[str, Any], questions_and_answers: List[Dict[str, str]]) -> str:
        """Create prompt for evaluating candidate answers"""
        qa_text = "\n\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in questions_and_answers])
        
        return f"""You are an expert technical interviewer evaluating candidate responses for a {job.get('title', 'N/A')} position.

Job Context:
- Required Skills: {', '.join(job.get('criteria', {}).get('skills', []))}
- Experience Level: {job.get('criteria', {}).get('exp_min', 0)}-{job.get('criteria', {}).get('exp_max', 10)} years
- Job Description: {job.get('jd_text', '')[:300]}...

Interview Questions and Answers:
{qa_text}

Evaluate each answer and provide:
1. Individual scores (0.0 to 1.0) for each question
2. Explanation for each score
3. Overall interview score (0.0 to 1.0)
4. Overall assessment

Return evaluation as JSON:
{{
    "question_scores": [0.8, 0.6, 0.9, ...],
    "question_explanations": ["Explanation for Q1", "Explanation for Q2", ...],
    "overall_score": 0.75,
    "overall_assessment": "Comprehensive assessment of candidate performance",
    "strengths": ["List of demonstrated strengths"],
    "areas_for_improvement": ["Areas needing development"]
}}

Scoring Guidelines:
- Technical accuracy and depth of knowledge
- Problem-solving approach and reasoning
- Communication clarity and structure
- Relevance to job requirements
- Experience level appropriateness

JSON Response:"""
    
    def _extract_json_response(self, response: str) -> Any:
        """Extracts a JSON object or array from the model's response string."""
        try:
            import re
            # Greedily find the largest JSON object or array
            json_match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return None

    def _extract_questions(self, response: str) -> List[str]:
        """Extract questions from the model's response"""
        questions = self._extract_json_response(response)
        if isinstance(questions, list) and all(isinstance(q, str) for q in questions):
            return questions
        # Fallback for non-JSON or incorrect format
        return [
            "Tell me about your experience with the technologies mentioned in this role.",
            "Describe a challenging project you've worked on and how you solved it.",
            "How do you approach learning new technologies?",
            "Walk me through your problem-solving process for complex technical issues.",
            "What interests you most about this position?"
        ]
    
    def _extract_evaluation(self, response: str) -> Dict[str, Any]:
        """Extract evaluation from the model's response"""
        evaluation = self._extract_json_response(response)
        if isinstance(evaluation, dict):
            return evaluation
        # Fallback: create minimal evaluation
        return {
            "question_scores": [0.5] * 5,
            "question_explanations": ["Evaluation error"] * 5,
            "overall_score": 0.5,
            "overall_assessment": "Unable to evaluate responses",
            "strengths": [],
            "areas_for_improvement": []
        }