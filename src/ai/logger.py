"""Logging configuration for AI insights module."""

from src.core.logging import get_logger

# Create logger for AI module
ai_logger = get_logger("ai_insights")


def log_ai_request(insight_type: str, system_id: str, **kwargs) -> None:
    """Log AI service request."""
    ai_logger.info(
        "AI request initiated",
        insight_type=insight_type,
        system_id=system_id,
        **kwargs
    )


def log_ai_response(insight_type: str, system_id: str, cached: bool, **kwargs) -> None:
    """Log AI service response."""
    ai_logger.info(
        "AI response generated",
        insight_type=insight_type,
        system_id=system_id,
        cached=cached,
        **kwargs
    )


def log_ai_error(insight_type: str, system_id: str, error: str, **kwargs) -> None:
    """Log AI service error."""
    ai_logger.error(
        "AI request failed",
        insight_type=insight_type,
        system_id=system_id,
        error=error,
        **kwargs
    )


def log_cache_operation(operation: str, cache_key: str, **kwargs) -> None:
    """Log cache operation."""
    ai_logger.debug(
        "Cache operation",
        operation=operation,
        cache_key=cache_key,
        **kwargs
    )
