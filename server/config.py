from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    '''Loads configuration from environment variables or .env file.'''
    SECRET_KEY: str
    ALGORITHM: str
    TOKEN_EXPIRE_HOURS: int
    DATABASE_URL: str

    model_config = {"env_file": ".env"}


settings = Settings()
