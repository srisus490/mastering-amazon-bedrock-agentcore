"""Cost monitoring for Bedrock API usage."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class CostMonitor:
    """Monitors and tracks Bedrock API costs."""
    
    # Pricing (per 1K tokens) - Claude 3 Sonnet
    INPUT_TOKEN_COST = 0.003
    OUTPUT_TOKEN_COST = 0.015
    CACHED_INPUT_TOKEN_COST = 0.0003
    
    # Thresholds
    HOURLY_TOKEN_THRESHOLD = 100000
    DEFAULT_DAILY_COST_THRESHOLD = 50.0  # $50 per day
    
    def __init__(self, daily_cost_threshold: Optional[float] = None):
        """
        Initialize cost monitor.
        
        Args:
            daily_cost_threshold: Maximum daily cost in USD (defaults to $50)
        """
        self.daily_cost_threshold = daily_cost_threshold or self.DEFAULT_DAILY_COST_THRESHOLD
        
        # Track token usage by hour and day
        self._hourly_tokens: Dict[str, int] = defaultdict(int)
        self._daily_tokens: Dict[str, int] = defaultdict(int)
        self._daily_costs: Dict[str, float] = defaultdict(float)
        
        # Circuit breaker state
        self._circuit_breaker_active = False
        self._circuit_breaker_date: Optional[str] = None
        
        logger.info(
            "Cost monitor initialized",
            daily_threshold=self.daily_cost_threshold,
            hourly_token_threshold=self.HOURLY_TOKEN_THRESHOLD
        )
    
    def recordTokenUsage(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> Dict[str, any]:
        """
        Record token usage and calculate costs.
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            cached_tokens: Number of cached input tokens
            
        Returns:
            Dictionary with cost information and alerts
        """
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        
        # Calculate costs
        input_cost = (input_tokens / 1000) * self.INPUT_TOKEN_COST
        output_cost = (output_tokens / 1000) * self.OUTPUT_TOKEN_COST
        cached_cost = (cached_tokens / 1000) * self.CACHED_INPUT_TOKEN_COST
        total_cost = input_cost + output_cost + cached_cost
        
        # Update tracking
        total_tokens = input_tokens + output_tokens
        self._hourly_tokens[hour_key] += total_tokens
        self._daily_tokens[day_key] += total_tokens
        self._daily_costs[day_key] += total_cost
        
        # Check thresholds
        alerts = []
        
        # Hourly token threshold
        if self._hourly_tokens[hour_key] > self.HOURLY_TOKEN_THRESHOLD:
            alert_msg = f"Hourly token threshold exceeded: {self._hourly_tokens[hour_key]:,} tokens"
            alerts.append(alert_msg)
            logger.warning(alert_msg, hour=hour_key, tokens=self._hourly_tokens[hour_key])
        
        # Daily cost threshold
        if self._daily_costs[day_key] > self.daily_cost_threshold:
            if not self._circuit_breaker_active or self._circuit_breaker_date != day_key:
                self._circuit_breaker_active = True
                self._circuit_breaker_date = day_key
                alert_msg = f"Daily cost threshold exceeded: ${self._daily_costs[day_key]:.2f}"
                alerts.append(alert_msg)
                logger.error(
                    "Circuit breaker activated - daily cost threshold exceeded",
                    day=day_key,
                    cost=self._daily_costs[day_key],
                    threshold=self.daily_cost_threshold
                )
        
        # Log usage
        logger.info(
            "Token usage recorded",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_tokens=cached_tokens,
            cost=total_cost,
            hourly_total=self._hourly_tokens[hour_key],
            daily_total=self._daily_tokens[day_key],
            daily_cost=self._daily_costs[day_key]
        )
        
        return {
            'cost': total_cost,
            'hourly_tokens': self._hourly_tokens[hour_key],
            'daily_tokens': self._daily_tokens[day_key],
            'daily_cost': self._daily_costs[day_key],
            'alerts': alerts,
            'circuit_breaker_active': self._circuit_breaker_active
        }
    
    def isCircuitBreakerActive(self) -> bool:
        """
        Check if circuit breaker is active.
        
        Returns:
            True if circuit breaker is active, False otherwise
        """
        # Reset circuit breaker if it's a new day
        if self._circuit_breaker_active:
            today = datetime.now().strftime("%Y-%m-%d")
            if self._circuit_breaker_date != today:
                self._circuit_breaker_active = False
                self._circuit_breaker_date = None
                logger.info("Circuit breaker reset for new day")
        
        return self._circuit_breaker_active
    
    def resetCircuitBreaker(self) -> None:
        """Manually reset the circuit breaker."""
        self._circuit_breaker_active = False
        self._circuit_breaker_date = None
        logger.info("Circuit breaker manually reset")
    
    def estimateQueryCost(
        self,
        estimated_input_tokens: int,
        estimated_output_tokens: int
    ) -> float:
        """
        Estimate cost for a query before execution.
        
        Args:
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (estimated_input_tokens / 1000) * self.INPUT_TOKEN_COST
        output_cost = (estimated_output_tokens / 1000) * self.OUTPUT_TOKEN_COST
        return input_cost + output_cost
    
    def getHourlyStats(self, hour_key: Optional[str] = None) -> Dict[str, any]:
        """
        Get statistics for a specific hour.
        
        Args:
            hour_key: Hour key in format "YYYY-MM-DD-HH" (defaults to current hour)
            
        Returns:
            Dictionary with hourly statistics
        """
        if hour_key is None:
            hour_key = datetime.now().strftime("%Y-%m-%d-%H")
        
        tokens = self._hourly_tokens.get(hour_key, 0)
        
        return {
            'hour': hour_key,
            'tokens': tokens,
            'threshold': self.HOURLY_TOKEN_THRESHOLD,
            'threshold_exceeded': tokens > self.HOURLY_TOKEN_THRESHOLD,
            'percentage': (tokens / self.HOURLY_TOKEN_THRESHOLD) * 100
        }
    
    def getDailyStats(self, day_key: Optional[str] = None) -> Dict[str, any]:
        """
        Get statistics for a specific day.
        
        Args:
            day_key: Day key in format "YYYY-MM-DD" (defaults to today)
            
        Returns:
            Dictionary with daily statistics
        """
        if day_key is None:
            day_key = datetime.now().strftime("%Y-%m-%d")
        
        tokens = self._daily_tokens.get(day_key, 0)
        cost = self._daily_costs.get(day_key, 0.0)
        
        return {
            'day': day_key,
            'tokens': tokens,
            'cost': cost,
            'threshold': self.daily_cost_threshold,
            'threshold_exceeded': cost > self.daily_cost_threshold,
            'percentage': (cost / self.daily_cost_threshold) * 100
        }
    
    def cleanOldData(self, days_to_keep: int = 7) -> None:
        """
        Clean up old tracking data.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_day = cutoff_date.strftime("%Y-%m-%d")
        cutoff_hour = cutoff_date.strftime("%Y-%m-%d-%H")
        
        # Clean hourly data
        old_hours = [k for k in self._hourly_tokens.keys() if k < cutoff_hour]
        for hour in old_hours:
            del self._hourly_tokens[hour]
        
        # Clean daily data
        old_days = [k for k in self._daily_tokens.keys() if k < cutoff_day]
        for day in old_days:
            del self._daily_tokens[day]
            if day in self._daily_costs:
                del self._daily_costs[day]
        
        if old_hours or old_days:
            logger.info(
                f"Cleaned old cost data",
                hours_removed=len(old_hours),
                days_removed=len(old_days)
            )


# Global cost monitor instance
_global_monitor = None


def get_cost_monitor() -> CostMonitor:
    """
    Get the global cost monitor instance.
    
    Returns:
        CostMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = CostMonitor()
    return _global_monitor
