# Import BaseSettings to manage environment variables
from pydantic_settings import BaseSettings

# Create a Settings class to store all config
class Settings(BaseSettings):
    # This prefix for every route
    PREFIX: str
    # MongoDB connection string (we will use this later)
    MONGODB_URL: str
    # MongoDB Database name
    DATABASE_NAME: str

    USER_COLLECTION: str

    # JWT secret key (used for signing tokens)
    JWT_SECRET: str

    # Algorithm used for JWT
    JWT_ALGORITHM: str = "HS256"

    # Access token expiry (in minutes)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1

    # Refresh token expiry (in days)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Tell Pydantic to read from .env file
    class Config:
        env_file = ".env"

# Create a single settings instance to use everywhere
settings = Settings()