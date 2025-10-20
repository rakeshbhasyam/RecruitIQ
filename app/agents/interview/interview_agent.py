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
    
    async def start_interview_session(self, candidate_id: str, job_id: str, 
                                    max_questions: int = 5, trace_id: str = None) -> Dict[str, Any]:
        """Start a new streaming interview session"""
        if not trace_id:
            import uuid
            trace_id = str(uuid.uuid4())
        
        try:
            # Get candidate and job data
            candidate = await db.candidates.get_candidate(candidate_id)
            job = await db.jobs.get_job(job_id)
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Create initial session
            session_data = {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "max_questions": max_questions,
                "interview_type": "technical"
            }
            
            session_id = await db.interview_sessions.create_session(session_data)
            
            # Generate first question
            first_question = await self._generate_next_question(
                candidate, job, [], session_id, trace_id
            )
            
            # Store the first question in the session context
            await db.interview_sessions.update_context(session_id, {
                "current_question": first_question,
                "question_index": 0
            })
            
            # Log the session start
            await self.log_activity(
                trace_id=trace_id,
                prompt=f"Started interview session for candidate {candidate_id}",
                tools_used=["gemini"],
                candidate_id=candidate_id,
                job_id=job_id,
                metadata={"session_id": session_id}
            )
            
            return {
                "session_id": session_id,
                "first_question": first_question,
                "question_index": 0,
                "is_complete": False,
                "context": {}
            }
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id,
                job_id=job_id
            )
            raise e
    
    async def get_next_question(self, session_id: str, answer: Optional[str] = None, 
                               trace_id: str = None) -> Dict[str, Any]:
        """Get the next question in the interview session"""
        if not trace_id:
            import uuid
            trace_id = str(uuid.uuid4())
        
        try:
            # Get session
            session = await db.interview_sessions.get_session(session_id)
            if not session:
                raise ValueError("Interview session not found")
            
            # If answer provided, evaluate and store it
            if answer:
                await self._process_answer(session, answer, trace_id)
            
            # Check if interview is complete
            if session["current_question_index"] >= session["max_questions"]:
                # Complete the interview
                await self._complete_interview(session, trace_id)
                return {
                    "session_id": session_id,
                    "question": None,
                    "question_index": session["current_question_index"],
                    "is_complete": True,
                    "context": session.get("context", {}),
                    "overall_score": session.get("overall_score"),
                    "overall_assessment": session.get("overall_assessment")
                }
            
            # Get candidate and job data
            candidate = await db.candidates.get_candidate(session["candidate_id"])
            job = await db.jobs.get_job(session["job_id"])
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Generate next question
            next_question = await self._generate_next_question(
                candidate, job, session["questions_and_answers"], session_id, trace_id
            )
            
            return {
                "session_id": session_id,
                "question": next_question,
                "question_index": session["current_question_index"],
                "is_complete": False,
                "context": session.get("context", {})
            }
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=session.get("candidate_id") if session else None,
                job_id=session.get("job_id") if session else None
            )
            raise e
    
    async def _generate_next_question(self, candidate: Dict[str, Any], job: Dict[str, Any], 
                                    previous_qa: List[Dict[str, Any]], session_id: str, 
                                    trace_id: str) -> str:
        """Generate the next question based on context"""
        # Create adaptive prompt
        prompt = self._create_adaptive_question_prompt(candidate, job, previous_qa)
        
        # Log the request
        await self.log_activity(
            trace_id=trace_id,
            prompt=prompt[:500] + "...",
            tools_used=["gemini"],
            candidate_id=candidate.get("_id"),
            job_id=job.get("_id"),
            metadata={"session_id": session_id}
        )
        
        # Call Gemini to generate question
        response = await self.call_gemini(prompt, max_tokens=500)
        
        # Extract question from response
        question = self._extract_single_question(response)
        
        # Log successful completion
        await self.log_activity(
            trace_id=trace_id,
            response=question,
            candidate_id=candidate.get("_id"),
            job_id=job.get("_id"),
            metadata={"session_id": session_id}
        )
        
        return question
    
    async def _process_answer(self, session: Dict[str, Any], answer: str, trace_id: str):
        """Process and evaluate a candidate's answer"""
        try:
            # Get job data for evaluation
            job = await db.jobs.get_job(session["job_id"])
            if not job:
                raise ValueError("Job not found")
            
            # Get the current question being answered
            if not session["questions_and_answers"]:
                # This is the first question - get it from session context
                question = session.get("context", {}).get("current_question", 
                    "Tell me about your experience with the technologies mentioned in this role.")
            else:
                # Get the last question (should be the one being answered)
                last_qa = session["questions_and_answers"][-1]
                question = last_qa["question"]
            
            # Evaluate the answer
            evaluation = await self._evaluate_single_answer(
                question, answer, job, session["questions_and_answers"][:-1], trace_id
            )
            
            # Add the Q&A pair to session
            await db.interview_sessions.add_question_answer(
                session["_id"], question, answer, 
                evaluation.get("score"), evaluation.get("explanation")
            )
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=session.get("candidate_id"),
                job_id=session.get("job_id")
            )
            raise e
    
    async def _evaluate_single_answer(self, question: str, answer: str, job: Dict[str, Any], 
                                    previous_qa: List[Dict[str, Any]], trace_id: str) -> Dict[str, Any]:
        """Evaluate a single answer"""
        # Create evaluation prompt
        prompt = self._create_single_answer_evaluation_prompt(question, answer, job, previous_qa)
        
        # Log the evaluation request
        await self.log_activity(
            trace_id=trace_id,
            prompt=prompt[:500] + "...",
            tools_used=["gemini"],
            candidate_id=job.get("_id")
        )
        
        # Call Gemini to evaluate
        response = await self.call_gemini(prompt, max_tokens=800)
        
        # Extract evaluation
        evaluation = self._extract_single_evaluation(response)
        
        return evaluation
    
    async def _complete_interview(self, session: Dict[str, Any], trace_id: str):
        """Complete the interview and calculate overall score"""
        try:
            # Get job data
            job = await db.jobs.get_job(session["job_id"])
            if not job:
                raise ValueError("Job not found")
            
            # Create overall evaluation prompt
            prompt = self._create_overall_evaluation_prompt(job, session["questions_and_answers"])
            
            # Log the completion request
            await self.log_activity(
                trace_id=trace_id,
                prompt=prompt[:500] + "...",
                tools_used=["gemini"],
                candidate_id=session.get("candidate_id"),
                job_id=session.get("job_id")
            )
            
            # Call Gemini for overall evaluation
            response = await self.call_gemini(prompt, max_tokens=1000)
            
            # Extract overall evaluation
            overall_evaluation = self._extract_overall_evaluation(response)
            
            # Complete the session
            await db.interview_sessions.complete_session(
                session["_id"],
                overall_evaluation.get("overall_score", 0.5),
                overall_evaluation.get("overall_assessment", "Interview completed")
            )
            
            # Update score in database
            interview_session = {
                "questions": [
                    {
                        "question": qa["question"],
                        "answer": qa["answer"],
                        "score": qa.get("score", 0.5),
                        "explanation": qa.get("explanation", "No explanation available")
                    }
                    for qa in session["questions_and_answers"]
                ],
                "overall_score": overall_evaluation.get("overall_score", 0.5),
                "duration_minutes": None,
                "notes": overall_evaluation.get("overall_assessment", "")
            }
            
            await db.scores.update_interview_score(session["candidate_id"], interview_session)
            
            # Log successful completion
            await self.log_activity(
                trace_id=trace_id,
                response=json.dumps(overall_evaluation, indent=2),
                metadata={"overall_score": overall_evaluation.get("overall_score")},
                candidate_id=session.get("candidate_id"),
                job_id=session.get("job_id")
            )
            
        except Exception as e:
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=session.get("candidate_id"),
                job_id=session.get("job_id")
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
    
    def _create_adaptive_question_prompt(self, candidate: Dict[str, Any], job: Dict[str, Any], 
                                         previous_qa: List[Dict[str, Any]]) -> str:
        """Create adaptive prompt for generating next question based on previous Q&A"""
        candidate_data = candidate.get("parsed_data", {})
        
        # Build context from previous Q&A
        context_text = ""
        if previous_qa:
            context_text = "\n\nPrevious Questions and Answers:\n"
            for i, qa in enumerate(previous_qa, 1):
                context_text += f"{i}. Q: {qa['question']}\n   A: {qa['answer']}\n"
        
        return f"""You are an expert technical interviewer conducting an adaptive interview. Generate the next question based on the candidate's previous answers.

Job Details:
- Title: {job.get('title', 'N/A')}
- Required Skills: {', '.join(job.get('criteria', {}).get('skills', []))}
- Experience Level: {job.get('criteria', {}).get('exp_min', 0)}-{job.get('criteria', {}).get('exp_max', 10)} years
- Job Description: {job.get('jd_text', '')[:500]}...

Candidate Profile:
- Skills: {', '.join(candidate_data.get('skills', []))}
- Experience: {candidate_data.get('experience', 0)} years
- Previous Roles: {', '.join(candidate_data.get('job_titles', []))}
{context_text}

Generate ONE follow-up question that:
1. Builds on the candidate's previous answers
2. Tests deeper technical knowledge based on their responses
3. Explores areas not yet covered
4. Is appropriate for their experience level
5. Relates to the job requirements

The question should be:
- Specific and technical
- Open-ended to allow detailed responses
- Progressive in difficulty
- Relevant to the role

Return ONLY the question text, no additional formatting or explanation.

Question:"""

    def _create_single_answer_evaluation_prompt(self, question: str, answer: str, job: Dict[str, Any], 
                                               previous_qa: List[Dict[str, Any]]) -> str:
        """Create prompt for evaluating a single answer"""
        # Build context from previous Q&A
        context_text = ""
        if previous_qa:
            context_text = "\n\nPrevious Questions and Answers:\n"
            for i, qa in enumerate(previous_qa, 1):
                context_text += f"{i}. Q: {qa['question']}\n   A: {qa['answer']}\n"
        
        return f"""You are an expert technical interviewer evaluating a candidate's answer.

Job Context:
- Title: {job.get('title', 'N/A')}
- Required Skills: {', '.join(job.get('criteria', {}).get('skills', []))}
- Experience Level: {job.get('criteria', {}).get('exp_min', 0)}-{job.get('criteria', {}).get('exp_max', 10)} years
{context_text}

Current Question and Answer:
Q: {question}
A: {answer}

Evaluate this answer and provide:
1. A score from 0.0 to 1.0
2. A brief explanation of the score
3. Key strengths demonstrated
4. Areas for improvement

Return evaluation as JSON:
{{
    "score": 0.8,
    "explanation": "Detailed explanation of the evaluation",
    "strengths": ["List of demonstrated strengths"],
    "areas_for_improvement": ["Areas needing development"]
}}

Scoring Guidelines:
- Technical accuracy and depth
- Problem-solving approach
- Communication clarity
- Relevance to job requirements
- Experience level appropriateness

JSON Response:"""

    def _create_overall_evaluation_prompt(self, job: Dict[str, Any], questions_and_answers: List[Dict[str, Any]]) -> str:
        """Create prompt for overall interview evaluation"""
        qa_text = "\n\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in questions_and_answers])
        
        return f"""You are an expert technical interviewer providing a comprehensive evaluation of the entire interview.

Job Context:
- Title: {job.get('title', 'N/A')}
- Required Skills: {', '.join(job.get('criteria', {}).get('skills', []))}
- Experience Level: {job.get('criteria', {}).get('exp_min', 0)}-{job.get('criteria', {}).get('exp_max', 10)} years

Complete Interview:
{qa_text}

Provide a comprehensive evaluation including:
1. Overall score (0.0 to 1.0)
2. Overall assessment
3. Key strengths demonstrated
4. Areas for improvement
5. Recommendation for next steps

Return evaluation as JSON:
{{
    "overall_score": 0.75,
    "overall_assessment": "Comprehensive assessment of candidate performance",
    "strengths": ["List of demonstrated strengths"],
    "areas_for_improvement": ["Areas needing development"],
    "recommendation": "Recommendation for next steps"
}}

JSON Response:"""

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
    
    def _extract_single_question(self, response: str) -> str:
        """Extract a single question from the model's response"""
        # Clean up the response
        question = response.strip()
        # Remove any JSON formatting or extra text
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        return question
    
    def _extract_single_evaluation(self, response: str) -> Dict[str, Any]:
        """Extract single answer evaluation from the model's response"""
        evaluation = self._extract_json_response(response)
        if isinstance(evaluation, dict):
            return evaluation
        # Fallback: create minimal evaluation
        return {
            "score": 0.5,
            "explanation": "Unable to evaluate response",
            "strengths": [],
            "areas_for_improvement": []
        }
    
    def _extract_overall_evaluation(self, response: str) -> Dict[str, Any]:
        """Extract overall evaluation from the model's response"""
        evaluation = self._extract_json_response(response)
        if isinstance(evaluation, dict):
            return evaluation
        # Fallback: create minimal evaluation
        return {
            "overall_score": 0.5,
            "overall_assessment": "Unable to evaluate interview",
            "strengths": [],
            "areas_for_improvement": [],
            "recommendation": "Further evaluation needed"
        }

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