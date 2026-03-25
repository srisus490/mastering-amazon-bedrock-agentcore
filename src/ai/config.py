"""Configuration for AI insights service."""

import os
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class AIConfig(BaseSettings):
    """Configuration for AI service (Cohere)."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env file
    )

    # Cohere settings
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    cohere_model: str = os.getenv("COHERE_MODEL", "command-r-plus-08-2024")

    # Kept for backward-compat (timeout / token / temperature reused by CohereClient)
    bedrock_region: str = os.getenv("BEDROCK_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv(
        "BEDROCK_MODEL_ID",
        "anthropic.claude-3-sonnet-20240229-v1:0"
    )
    bedrock_timeout: int = int(os.getenv("BEDROCK_TIMEOUT", "30"))
    bedrock_max_tokens: int = int(os.getenv("BEDROCK_MAX_TOKENS", "4000"))
    bedrock_temperature: float = float(os.getenv("BEDROCK_TEMPERATURE", "0.7"))
    
    # Knowledge Base settings
    knowledge_base_id: Optional[str] = os.getenv("KNOWLEDGE_BASE_ID")
    knowledge_base_region: str = os.getenv("KNOWLEDGE_BASE_REGION", "us-east-1")
    kb_max_results: int = int(os.getenv("KB_MAX_RESULTS", "5"))
    kb_similarity_threshold: float = float(os.getenv("KB_SIMILARITY_THRESHOLD", "0.7"))
    
    # Cache TTL settings (in seconds)
    ai_cache_ttl_insights: int = int(os.getenv("AI_CACHE_TTL_INSIGHTS", "3600"))  # 1 hour
    ai_cache_ttl_forecast: int = int(os.getenv("AI_CACHE_TTL_FORECAST", "21600"))  # 6 hours
    ai_cache_ttl_root_cause: int = int(os.getenv("AI_CACHE_TTL_ROOT_CAUSE", "3600"))  # 1 hour
    
    # Feature flags
    ai_enabled: bool = os.getenv("AI_ENABLED", "true").lower() == "true"
    
    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return self.ai_enabled and bool(self.cohere_api_key)


# Global config instance
ai_config = AIConfig()


def get_ai_config() -> dict:
    """Get AI configuration as dictionary."""
    return {
        'COHERE_MODEL': ai_config.cohere_model,
        'COHERE_API_KEY_SET': bool(ai_config.cohere_api_key),
        'BEDROCK_TIMEOUT': ai_config.bedrock_timeout,
        'BEDROCK_MAX_TOKENS': ai_config.bedrock_max_tokens,
        'BEDROCK_TEMPERATURE': ai_config.bedrock_temperature,
        'KNOWLEDGE_BASE_ID': ai_config.knowledge_base_id,
        'KNOWLEDGE_BASE_REGION': ai_config.knowledge_base_region,
        'KB_MAX_RESULTS': ai_config.kb_max_results,
        'KB_SIMILARITY_THRESHOLD': ai_config.kb_similarity_threshold,
        'AI_ENABLED': ai_config.ai_enabled
    }
