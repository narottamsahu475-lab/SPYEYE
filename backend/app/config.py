from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEOCODING_API_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_API_URL: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    CACHE_EXPIRATION_SECONDS: int = 900  # 15 minutes

    class Config:
        env_file = ".env"

settings = Settings()
