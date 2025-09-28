import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "agentic_recruitment")
    
    # API settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "5000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Anthropic settings
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Security
    session_secret: str = os.getenv("SESSION_SECRET", "")
    
    class Config:
        env_file = ".env"

settings = Settings()