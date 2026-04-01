from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_NAME: str = "AssemblPro - Votação Eletrônica Segura"
    APP_URL: str = "http://localhost:8033"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    # OTP
    OTP_EXPIRATION_SECONDS: int = 300

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
