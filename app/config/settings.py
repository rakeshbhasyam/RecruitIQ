import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Load .env file first
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database settings
    mongodb_url: str = Field(..., alias="MONGODB_URL")
    database_name: str = Field(default="agentic_recruitment", alias="DATABASE_NAME")

    # API settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=5000, alias="API_PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Google Gemini API key
    google_api_key: str = Field(..., alias="GEMINI_API_KEY")


settings = Settings()

# Set the environment variable explicitly for Gemini SDK
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

