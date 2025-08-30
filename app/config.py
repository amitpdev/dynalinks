from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Domain Configuration
    base_domain: str
    short_domain: str
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Analytics
    enable_analytics: bool = True
    
    # GeoIP
    geoip_db_path: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
