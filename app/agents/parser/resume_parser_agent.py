import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date
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
                tools_used=["gemini"],
                candidate_id=candidate_id
            )
            
            # Call Gemini to parse the resume
            response = await self.call_gemini(prompt, max_tokens=1500)
            
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
        current_date = datetime.now().strftime("%Y-%m-%d")
        return f"""You are an expert resume parser. Extract comprehensive structured information from the following resume text and return it as a JSON object.

Current Date: {current_date}

Resume Text:
{extracted_text}

Please extract the following information and return it as a valid JSON object:
{{
    "name": "Candidate's full name",
    "skills": ["List of ALL technical skills, programming languages, frameworks, tools, databases, etc."],
    "experience_years": "Total years of professional experience as an integer",
    "education": "Highest degree and institution with details",
    "job_titles": ["List of ALL previous job titles"],
    "projects": [
        {{
            "name": "Project name",
            "description": "Project description",
            "technologies": ["Technologies used"],
            "url": "Project URL if available"
        }}
    ],
    "certifications": ["List of ALL certifications with details"],
    "summary": "Professional summary or objective if available",
    "contact_info": {{
        "email": "email address if found",
        "phone": "phone number if found", 
        "location": "location/city if found",
        "linkedin": "LinkedIn profile URL if found",
        "github": "GitHub profile URL if found"
    }},
    "work_experience": [
        {{
            "title": "Job title",
            "company": "Company name",
            "duration": "Duration/date range",
            "description": "Job description and responsibilities",
            "achievements": ["Key achievements and accomplishments"],
            "technologies": ["Technologies used in this role"]
        }}
    ],
    "additional_info": {{
        "languages": ["Languages spoken"],
        "interests": ["Professional interests"],
        "awards": ["Awards and honors"],
        "publications": ["Publications if any"]
    }}
}}

Important instructions:
1. Return ONLY the JSON object, no additional text
2. If information is not found, use null for strings, empty arrays for lists, and 0 for experience_years
3. Extract skills comprehensively - include programming languages, frameworks, tools, databases, cloud platforms, etc.
4. For projects, extract ALL projects mentioned with full details:
   - Look for actual GitHub URLs (https://github.com/username/repo or github.com/username/repo)
   - Extract project names, descriptions, and technologies used
   - If no real URL is found, set url to null (not "GitHubRepo/" or similar placeholders)
5. For work_experience, extract detailed information for each job including achievements:
   - Calculate duration in months/years from start to end dates (use current date if still working)
   - Include internships, part-time jobs, and full-time positions
   - Extract all technologies used in each role
6. Look for LinkedIn and GitHub URLs in the text and include them in contact_info
7. Calculate experience_years based on job history dates using the current date ({current_date}):
   - Convert all durations to years (e.g., 6 months = 0.5 years, 18 months = 1.5 years)
   - Sum up all professional experience including internships
8. Extract ALL certifications and awards mentioned
9. Ensure the JSON is valid and properly formatted
10. Be thorough - extract as much information as possible
11. For contact_info, include the candidate's name in the name field
12. For projects, prioritize GitHub URLs as the project URL

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
                "experience_years": 0,
                "education": None,
                "job_titles": [],
                "projects": [],
                "certifications": [],
                "summary": None,
                "contact_info": {},
                "work_experience": [],
                "additional_info": {}
            }
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean parsed data"""
        work_experience = self._clean_work_experience(data.get("work_experience", []))
        
        # Calculate experience years from work experience if not provided or if it's 0
        experience_years = data.get("experience_years", 0)
        if not experience_years or experience_years == 0:
            experience_years = self._calculate_experience_years(work_experience)
        else:
            # Ensure it's a number
            try:
                experience_years = float(experience_years)
            except (ValueError, TypeError):
                experience_years = self._calculate_experience_years(work_experience)
        
        cleaned = {
            "name": data.get("name"),
            "skills": self._clean_skills_list(data.get("skills", [])),
            "experience_years": max(0, experience_years),
            "education": data.get("education"),
            "job_titles": [title for title in data.get("job_titles", []) if title],
            "projects": self._clean_projects_list(data.get("projects", [])),
            "certifications": [cert for cert in data.get("certifications", []) if cert],
            "summary": data.get("summary"),
            "contact_info": self._clean_contact_info(data.get("contact_info", {})),
            "work_experience": work_experience,
            "additional_info": data.get("additional_info", {})
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
    
    def _clean_projects_list(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and normalize projects list"""
        if not isinstance(projects, list):
            return []
        
        cleaned_projects = []
        for project in projects:
            if isinstance(project, dict):
                url = project.get("url", "")
                # Clean up URL - if it's a placeholder or invalid, set to None
                if not url or url in ["GitHubRepo/", "github.com/", "https://github.com/", ""]:
                    url = None
                elif not url.startswith(("http://", "https://", "github.com/")):
                    # If it doesn't look like a real URL, set to None
                    url = None
                
                cleaned_project = {
                    "name": project.get("name", ""),
                    "description": project.get("description", ""),
                    "technologies": [tech for tech in project.get("technologies", []) if tech],
                    "url": url
                }
                if cleaned_project["name"]:  # Only add if project has a name
                    cleaned_projects.append(cleaned_project)
        
        return cleaned_projects
    
    def _clean_contact_info(self, contact_info: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize contact info"""
        if not isinstance(contact_info, dict):
            return {}
        
        return {
            "email": contact_info.get("email"),
            "phone": contact_info.get("phone"),
            "location": contact_info.get("location"),
            "linkedin": contact_info.get("linkedin"),
            "github": contact_info.get("github")
        }
    
    def _clean_work_experience(self, work_experience: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and normalize work experience list"""
        if not isinstance(work_experience, list):
            return []
        
        cleaned_experience = []
        for exp in work_experience:
            if isinstance(exp, dict):
                cleaned_exp = {
                    "title": exp.get("title", ""),
                    "company": exp.get("company", ""),
                    "duration": exp.get("duration", ""),
                    "description": exp.get("description", ""),
                    "achievements": [ach for ach in exp.get("achievements", []) if ach],
                    "technologies": [tech for tech in exp.get("technologies", []) if tech]
                }
                if cleaned_exp["title"]:  # Only add if job has a title
                    cleaned_experience.append(cleaned_exp)
        
        return cleaned_experience
    
    def _calculate_experience_years(self, work_experience: List[Dict[str, Any]]) -> float:
        """Calculate total experience years from work experience"""
        if not work_experience:
            return 0.0
        
        total_months = 0
        current_date = datetime.now()
        
        for exp in work_experience:
            duration = exp.get("duration", "")
            if not duration:
                continue
                
            # Try to extract months from duration string
            months = self._extract_months_from_duration(duration, current_date)
            total_months += months
        
        # Convert months to years
        return round(total_months / 12, 1)
    
    def _extract_months_from_duration(self, duration: str, current_date: datetime) -> int:
        """Extract months from duration string"""
        duration_lower = duration.lower()
        
        # Handle "Present" or "Current"
        if "present" in duration_lower or "current" in duration_lower:
            # Look for start date
            import re
            year_match = re.search(r'(\d{4})', duration)
            if year_match:
                start_year = int(year_match.group(1))
                months = (current_date.year - start_year) * 12 + (current_date.month - 1)
                return max(0, months)
        
        # Handle month patterns
        month_patterns = [
            (r'(\d+)\s*months?', 1),
            (r'(\d+)\s*years?\s*(\d+)\s*months?', lambda m: int(m.group(1)) * 12 + int(m.group(2))),
            (r'(\d+)\s*years?', lambda m: int(m.group(1)) * 12),
            (r'(\d+)\s*yr', lambda m: int(m.group(1)) * 12),
            (r'(\d+)\s*mo', 1)
        ]
        
        for pattern, multiplier in month_patterns:
            match = re.search(pattern, duration_lower)
            if match:
                if callable(multiplier):
                    return multiplier(match)
                else:
                    return int(match.group(1)) * multiplier
        
        return 0