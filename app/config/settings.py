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
    mongodb_url: str = "mongodb+srv://phanivutla2004:phaniphani@cluster0.gddku.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true"
    database_name: str = "agentic_recruitment"

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 5000
    debug: bool = False

    # Google Gemini API key
    google_api_key: str = Field(..., alias="GEMINI_API_KEY")


settings = Settings()

# Set the environment variable explicitly for Gemini SDK
os.environ["GOOGLE_API_KEY"] = settings.google_api_key
