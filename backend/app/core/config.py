"""
PNMP Core Configuration
Loads settings from environment variables and .env file
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Application
    APP_NAME: str = "PNMP"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    APP_SECRET_KEY: str = "change-this-to-random-secret-key-min-32-chars"
    APP_DEBUG: bool = True
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://pnmp:password@localhost:5432/pnmp"
    
    # JWT
    JWT_SECRET_KEY: str = "change-this-to-another-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # SNMP
    SNMP_DEFAULT_TIMEOUT: int = 5
    SNMP_DEFAULT_RETRIES: int = 2
    SNMP_POLL_INTERVAL: int = 60
    
    # Zabbix
    ZABBIX_URL: str = ""
    ZABBIX_API_TOKEN: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
