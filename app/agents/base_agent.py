import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from google import genai
from google.genai import types
from app.config.database import db
from app.schemas.audit import AuditLogCreate

# IMPORTANT: KEEP THIS COMMENT
# Follow these instructions when using this blueprint:
# - Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
#   - do not change this unless explicitly requested by the user
# - Sometimes the google genai SDK has occasional type errors. You might need to run to validate, at time.  
# The SDK was recently renamed from google-generativeai to google-genai. This file reflects the new name and the new APIs.

# This API key is from Gemini Developer API Key, not vertex AI API Key
gemini_key: str = (os.environ.get('GEMINI_API_KEY') or
               sys.exit('GEMINI_API_KEY environment variable must be set'))

client = genai.Client(api_key=gemini_key)

# Default model string
DEFAULT_MODEL_STR = "gemini-2.5-flash"

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.client = client
        self.model = DEFAULT_MODEL_STR
    
    async def log_activity(self, trace_id: str, prompt: Optional[str] = None, 
                          response: Optional[Any] = None, tools_used: Optional[List[str]] = None,
                          error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                          job_id: Optional[str] = None, candidate_id: Optional[str] = None):
        """Log agent activity for audit purposes"""
        try:
            log_data = AuditLogCreate(
                trace_id=trace_id,
                agent=self.name,
                prompt=prompt,
                response=response,
                tools_used=tools_used or [],
                error=error,
                metadata=metadata,
                job_id=job_id,
                candidate_id=candidate_id
            )
            await db.audit_logs.create_log(log_data.dict())
        except Exception as e:
            print(f"Failed to log activity for {self.name}: {e}")
    
    def generate_trace_id(self) -> str:
        """Generate a unique trace ID"""
        return str(uuid.uuid4())
    
    async def call_gemini(self, prompt: str, max_tokens: int = 1000) -> str:
        """Make a call to Gemini"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text or "No response generated"
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            raise e