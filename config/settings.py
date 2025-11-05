"""
UBEC Protocol Website - Configuration Settings
==============================================

Centralized configuration management using environment variables and pydantic.

Implements:
    - Principle #4: Single Source of Truth
    - Principle #8: No Duplicate Configuration

Attribution:
    This project uses the services of Claude and Anthropic PBC to inform 
    our decisions and recommendations. This project was made possible with 
    the assistance of Claude and Anthropic PBC.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Principle #4: Single source of truth for configuration
    Principle #8: Each parameter defined exactly once
    """
    
    # ========================================================================
    # Application Settings
    # ========================================================================
    
    APP_ENV: str = Field(
        default="production",
        description="Application environment: development, staging, or production"
    )
    
    APP_HOST: str = Field(
        default="127.0.0.1",
        description="Host to bind the application to (use 127.0.0.1 for localhost only)"
    )
    
    APP_PORT: int = Field(
        default=8001,
        description="Port to run the application on"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    # ========================================================================
    # Backend API Configuration
    # ========================================================================
    
    BACKEND_API_URL: str = Field(
        default="http://localhost:8000",
        description="URL of the UBEC Protocol backend API"
    )
    
    BACKEND_API_KEY: str = Field(
        default="",
        description="API key for authenticating with backend (if required)"
    )
    
    # ========================================================================
    # Security Settings
    # ========================================================================
    
    SECRET_KEY: str = Field(
        default="change-this-in-production",
        description="Secret key for session management and CSRF protection"
    )
    
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:8001", "http://127.0.0.1:8001"],
        description="Allowed origins for CORS"
    )
    
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "bioregional.ubec.network", "ubec.network", "www.ubec.network"],
        description="Allowed hosts for the application"
    )
    
    # ========================================================================
    # Cache Settings
    # ========================================================================
    
    CACHE_TTL_SECONDS: int = Field(
        default=30,
        description="Default cache TTL for API responses in seconds"
    )
    
    CACHE_MAX_SIZE: int = Field(
        default=1000,
        description="Maximum number of items to store in cache"
    )
    
    # ========================================================================
    # Feature Flags
    # ========================================================================
    
    ENABLE_API_DOCS: bool = Field(
        default=True,
        description="Enable /api/docs and /api/redoc endpoints"
    )
    
    ENABLE_METRICS: bool = Field(
        default=False,
        description="Enable Prometheus metrics endpoint"
    )
    
    ENABLE_WEBSOCKETS: bool = Field(
        default=False,
        description="Enable WebSocket support for real-time updates"
    )
    
    # ========================================================================
    # Rate Limiting
    # ========================================================================
    
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Maximum requests per minute per IP"
    )
    
    # ========================================================================
    # Pydantic Configuration
    # ========================================================================
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    # ========================================================================
    # Validation Methods
    # ========================================================================
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.APP_ENV == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.APP_ENV == "production"
    
    def validate_security(self) -> List[str]:
        """
        Validate security settings and return warnings
        
        Returns:
            List of security warnings
        """
        warnings = []
        
        if self.is_production():
            if self.SECRET_KEY == "change-this-in-production":
                warnings.append("SECRET_KEY is using default value in production!")
            
            if self.APP_HOST == "0.0.0.0":
                warnings.append("APP_HOST is exposed to all interfaces (0.0.0.0)")
            
            if not self.BACKEND_API_KEY:
                warnings.append("BACKEND_API_KEY is empty - backend may be unprotected")
        
        return warnings


# Create settings instance
settings = Settings()

# Log security warnings on import
if settings.is_production():
    warnings = settings.validate_security()
    if warnings:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("SECURITY WARNINGS:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
