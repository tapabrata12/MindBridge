from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List,ClassVar

class Settings(BaseSettings):
    API_PREFIX : ClassVar[str] = '/api/v1'
    MONGODB_URL: str | None = None
    ALLOWED_ORIGINS: str = ''
    database_name: str | None = None
    gemini_api_key: str | None = None

    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def allowed_origins(cls, v: str)-> List[str]:
        return v.split(',') if v else []

    class Config:
        case_sensitive = False
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()