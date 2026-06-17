from pydantic_settings import BaseSettings


class ClientSettings(BaseSettings):
    SERVER_URL: str

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = ClientSettings()
