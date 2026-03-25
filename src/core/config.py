"""Configuration management using Pydantic Settings"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """SQLite database configuration - completely FREE!"""

    path: str = Field(
        default="data/file_monitoring.db", 
        description="SQLite database file path"
    )
    
    # Connection pool settings
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    pool_pre_ping: bool = Field(default=True, description="Verify connections before use")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    @property
    def url(self) -> str:
        """Get SQLite connection URL"""
        return f"sqlite:///{self.path}"


class AppConfig(BaseSettings):
    """Application configuration"""

    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    service_name: str = Field(
        default="file-monitoring", description="Service name for logging"
    )
    
    # API configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="Number of API workers")
    
    # JWT configuration
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="JWT secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(
        default=60, description="JWT token expiration in minutes"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings - Simplified PostgreSQL-only architecture"""

    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton pattern).
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment (useful for testing).
    
    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
