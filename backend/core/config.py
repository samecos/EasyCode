from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    KIMI_API_KEY: str
    KIMI_BASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
