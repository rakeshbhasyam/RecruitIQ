import re
import json
from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent
from app.config.database import db

class ResumeParserAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResumeParserAgent")
    
    async def parse_resume(self, candidate_id: str, extracted_text: str, trace_id: str) -> Dict[str, Any]:
        """Parse structured data from resume text using Claude"""
        try:
            # Create parsing prompt
            prompt = self._create_parsing_prompt(extracted_text)
            
            # Log the parsing request
            await self.log_activity(
                trace_id=trace_id,
                prompt=prompt[:500] + "...",  # Log first 500 chars
                tools_used=["anthropic_claude"],
                candidate_id=candidate_id
            )
            
            # Call Claude to parse the resume
            response = await self.call_anthropic(prompt, max_tokens=1500)
            
            # Parse the JSON response
            parsed_data = self._extract_json_from_response(response)
            
            # Validate and clean the parsed data
            cleaned_data = self._validate_and_clean_data(parsed_data)
            
            # Update candidate with parsed data
            await db.candidates.update_parsed_data(candidate_id, cleaned_data)
            
            # Log successful completion
            await self.log_activity(
                trace_id=trace_id,
                response=json.dumps(cleaned_data, indent=2),
                metadata={"skills_count": len(cleaned_data.get("skills", [])),
                         "experience_years": cleaned_data.get("experience", 0)},
                candidate_id=candidate_id
            )
            
            return cleaned_data
            
        except Exception as e:
            # Log error
            await self.log_activity(
                trace_id=trace_id,
                error=str(e),
                candidate_id=candidate_id
            )
            raise e
    
    def _create_parsing_prompt(self, extracted_text: str) -> str:
        """Create prompt for Claude to parse resume data"""
        return f"""You are an expert resume parser. Extract structured information from the following resume text and return it as a JSON object.

Resume Text:
{extracted_text}

Please extract the following information and return it as a valid JSON object:
{{
    "name": "Candidate's full name",
    "skills": ["List of technical skills, programming languages, tools, etc."],
    "experience": "Total years of professional experience as an integer",
    "education": "Highest degree and institution",
    "job_titles": ["List of previous job titles"],
    "certifications": ["List of certifications"],
    "contact_info": {{
        "email": "email address if found",
        "phone": "phone number if found",
        "location": "location/city if found"
    }}
}}

Important instructions:
1. Return ONLY the JSON object, no additional text
2. If information is not found, use null for strings, empty arrays for lists, and 0 for experience
3. Extract skills comprehensively including programming languages, frameworks, tools, databases, etc.
4. Calculate experience based on job history dates
5. Ensure the JSON is valid and properly formatted

JSON Response:"""
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON object from Claude's response"""
        try:
            # Find JSON object in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # If no JSON found, try to parse the entire response
                return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: create minimal structure
            return {
                "name": None,
                "skills": [],
                "experience": 0,
                "education": None,
                "job_titles": [],
                "certifications": [],
                "contact_info": {}
            }
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean parsed data"""
        cleaned = {
            "name": data.get("name"),
            "skills": self._clean_skills_list(data.get("skills", [])),
            "experience": max(0, int(data.get("experience", 0)) if isinstance(data.get("experience"), (int, str)) else 0),
            "education": data.get("education"),
            "job_titles": [title for title in data.get("job_titles", []) if title],
            "certifications": [cert for cert in data.get("certifications", []) if cert],
            "contact_info": data.get("contact_info", {})
        }
        return cleaned
    
    def _clean_skills_list(self, skills: List[str]) -> List[str]:
        """Clean and normalize skills list"""
        if not isinstance(skills, list):
            return []
        
        cleaned_skills = []
        for skill in skills:
            if isinstance(skill, str) and skill.strip():
                # Remove extra whitespace and normalize
                cleaned_skill = ' '.join(skill.strip().split())
                if cleaned_skill and cleaned_skill not in cleaned_skills:
                    cleaned_skills.append(cleaned_skill)
        
        return cleaned_skills