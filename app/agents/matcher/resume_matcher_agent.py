import json
from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent
from app.config.database import db

class ResumeMatcherAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResumeMatcherAgent")
    
    async def match_candidate(self, candidate_id: str, job_id: str, trace_id: str) -> Dict[str, Any]:
        """Match candidate resume against job requirements"""
        try:
            # Get candidate and job data
            candidate = await db.candidates.get_candidate(candidate_id)
            job = await db.jobs.get_job(job_id)
            
            if not candidate or not job:
                raise ValueError("Candidate or job not found")
            
            # Create matching prompt
            prompt = self._create_matching_prompt(candidate, job)
            
            # Log the matching request
            await self.log_activity(
                trace_id=trace_id,
                prompt=prompt[:500] + "...",
                tools_used=["gemini"],
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            # Call Gemini to perform matching
            response = await self.call_gemini(prompt, max_tokens=1000)
            
            # Parse the matching result
            matching_result = self._extract_matching_result(response)
            
            # Calculate final matcher score
            matcher_score = self._calculate_matcher_score(matching_result, job.get("criteria", {}))
            
            # Create score breakdown
            breakdown = {
                "skills_match": matching_result.get("skills_match_score", 0.0),
                "exp_match": matching_result.get("experience_match_score", 0.0)
            }
            
            # Update score in database
            await db.scores.update_matcher_score(candidate_id, matcher_score, breakdown)
            
            result = {
                "matcher_score": matcher_score,
                "breakdown": breakdown,
                "detailed_analysis": matching_result
            }
            
            # Log successful completion
            await self.log_activity(
                trace_id=trace_id,
                response=json.dumps(result, indent=2),
                metadata=result,
                candidate_id=candidate_id,
                job_id=job_id
            )
            
            return result
            
        except Exception as e:
            # Log error
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id,
                job_id=job_id
            )
            raise e
    
    def _create_matching_prompt(self, candidate: Dict[str, Any], job: Dict[str, Any]) -> str:
        """Create prompt for Claude to match candidate against job"""
        candidate_data = candidate.get("parsed_data", {})
        job_criteria = job.get("criteria", {})
        
        return f"""You are an expert HR recruiter. Analyze how well this candidate matches the job requirements.

Candidate Profile:
- Name: {candidate_data.get('name', 'N/A')}
- Skills: {', '.join(candidate_data.get('skills', []))}
- Experience: {candidate_data.get('experience', 0)} years
- Education: {candidate_data.get('education', 'N/A')}
- Previous Job Titles: {', '.join(candidate_data.get('job_titles', []))}

Job Requirements:
- Title: {job.get('title', 'N/A')}
- Required Skills: {', '.join(job_criteria.get('skills', []))}
- Experience Range: {job_criteria.get('exp_min', 0)}-{job_criteria.get('exp_max', 10)} years
- Job Description: {job.get('jd_text', '')[:500]}...

Please analyze the match and return a JSON object with the following structure:
{{
    "skills_match_score": "Score from 0.0 to 1.0 for skills alignment",
    "experience_match_score": "Score from 0.0 to 1.0 for experience fit",
    "skills_analysis": "Detailed analysis of skill matches and gaps",
    "experience_analysis": "Analysis of experience level fit",
    "overall_assessment": "Overall candidate fit summary",
    "strengths": ["List of candidate strengths"],
    "gaps": ["List of skill or experience gaps"]
}}

Scoring Guidelines:
- Skills match: Higher score for more required skills present and relevant
- Experience match: 1.0 for experience in range, lower for under/over qualified
- Consider transferable skills and domain relevance
- Be objective and thorough in your analysis

JSON Response:"""
    
    def _extract_matching_result(self, response: str) -> Dict[str, Any]:
        """Extract matching result from Claude's response"""
        try:
            import re
            # Find JSON object in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: create minimal structure
            return {
                "skills_match_score": 0.5,
                "experience_match_score": 0.5,
                "skills_analysis": "Error parsing analysis",
                "experience_analysis": "Error parsing analysis",
                "overall_assessment": "Analysis failed",
                "strengths": [],
                "gaps": []
            }
    
    def _calculate_matcher_score(self, matching_result: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate final matcher score based on weights"""
        weights = criteria.get("weights", {"skills": 0.7, "experience": 0.3})
        
        skills_score = matching_result.get("skills_match_score", 0.0)
        exp_score = matching_result.get("experience_match_score", 0.0)
        
        # Ensure scores are floats
        if isinstance(skills_score, str):
            try:
                skills_score = float(skills_score)
            except ValueError:
                skills_score = 0.0
        
        if isinstance(exp_score, str):
            try:
                exp_score = float(exp_score)
            except ValueError:
                exp_score = 0.0
        
        # Calculate weighted score
        final_score = (skills_score * weights.get("skills", 0.7) + 
                      exp_score * weights.get("experience", 0.3))
        
        return min(1.0, max(0.0, final_score))  # Ensure score is between 0 and 1