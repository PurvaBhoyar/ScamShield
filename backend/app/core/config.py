from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "ScamShield API"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "scamshield"
    GOOGLE_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
