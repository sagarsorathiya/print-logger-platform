"""
Application Configuration

Manages all configuration settings using Pydantic Settings.
Supports environment variables and .env files.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Application
    APP_NAME: str = "Print Tracking Portal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY_EXPIRE_HOURS: int = 24
    
    # Database
    DATABASE_URL: str = "sqlite:///./printportal.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000,http://127.0.0.1:3000"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # LDAP Configuration
    LDAP_ENABLED: bool = False
    LDAP_SERVER: Optional[str] = None
    LDAP_BIND_DN: Optional[str] = None
    LDAP_BIND_PASSWORD: Optional[str] = None
    LDAP_SEARCH_BASE: Optional[str] = None
    LDAP_USER_FILTER: str = "(sAMAccountName={username})"
    LDAP_GROUP_FILTER: str = "(member={user_dn})"
    
    # Agent Configuration
    AGENT_UPDATE_INTERVAL: int = 300  # seconds
    AGENT_OFFLINE_CACHE_DAYS: int = 7
    AGENT_MAX_LOG_SIZE_MB: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # Company Branding
    COMPANY_NAME: str = "Your Company"
    COMPANY_LOGO_URL: str = "/static/images/logo.png"
    
    # Email Configuration (optional)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [i.strip() for i in self.CORS_ORIGINS.split(",") if i.strip()]
        return self.CORS_ORIGINS
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "forbid"


# Create settings instance
settings = Settings()

# Ensure required directories exist
def ensure_directories():
    """Create required directories if they don't exist."""
    directories = [
        "logs",
        "static",
        "static/images",
        "uploads",
        "agent_cache"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Initialize directories on import
ensure_directories()
