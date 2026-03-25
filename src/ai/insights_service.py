"""AI Insights Service - Main orchestration for AI-powered insights."""

import json
from datetime import date, datetime, timedelta
from typing import Dict, Optional

from src.ai.cohere_client import (
    CohereClient,
    CohereError as BedrockError,
    CohereTimeoutError as BedrockTimeoutError,
    CohereUnavailableError as BedrockUnavailableError,
)
from src.ai.cache_manager import CacheManager
from src.ai.data_aggregator import DataAggregator
from src.ai.logger import ai_logger
from src.ai.prompt_builder import PromptBuilder


class AIInsightsService:
    """
    Service for generating AI-powered insights about file monitoring data.
    
    Orchestrates BedrockClient, CacheManager, DataAggregator, and PromptBuilder
    to provide smart insights, forecasts, and root cause analysis.
    """
    
    def __init__(
        self,
        bedrock_client: Optional[CohereClient] = None,
        cache_manager: Optional[CacheManager] = None,
        data_aggregator: Optional[DataAggregator] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ):
        """
        Initialize AI Insights Service.
        
        Args:
            bedrock_client: Bedrock client (creates new if None)
            cache_manager: Cache manager (creates new if None)
            data_aggregator: Data aggregator (creates new if None)
            prompt_builder: Prompt builder (creates new if None)
        """
        self.bedrock_client = bedrock_client or CohereClient()
        self.cache_manager = cache_manager or CacheManager()
        self.data_aggregator = data_aggregator or DataAggregator()
        self.prompt_builder = prompt_builder or PromptBuilder()
        
        ai_logger.info("AIInsightsService initialized")
    
    def generate_smart_insights(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Generate natural language insights about system health.
        
        Args:
            source_system_id: Source system identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with insights, trends, anomalies, recommendations
        """
        ai_logger.info(
            "Generating smart insights",
            source_system_id=source_system_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Generate cache key
        cache_key = self.cache_manager.generate_cache_key(
            "insights",
            source_system_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Check cache
        cached = self.cache_manager.get_cached_insight(cache_key)
        if cached:
            ai_logger.info("Returning cached insights", cache_key=cache_key)
            return cached
        
        try:
            # Aggregate data
            data_summary = self.data_aggregator.get_file_arrival_summary(
                source_system_id,
                start_date,
                end_date
            )
            
            # Build prompt
            prompt = self.prompt_builder.build_insights_prompt(data_summary)
            
            # Call AI service with retry
            response_text = self._invoke_with_retry(prompt)
            
            # Parse response
            insights = self._parse_insights_response(
                response_text,
                source_system_id,
                start_date,
                end_date
            )
            
            # Cache response
            ttl = self.cache_manager.get_ttl_for_insight_type("insights")
            self.cache_manager.set_cached_insight(cache_key, insights, ttl)
            
            ai_logger.info(
                "Smart insights generated successfully",
                source_system_id=source_system_id
            )
            
            return insights
            
        except (BedrockTimeoutError, BedrockUnavailableError) as e:
            # Try to return stale cache on service errors
            ai_logger.warning(
                "AI service error, attempting stale cache fallback",
                error=str(e)
            )
            stale_cache = self.cache_manager.get_cached_insight(
                cache_key,
                ignore_ttl=True
            )
            if stale_cache:
                ai_logger.info("Returning stale cached insights")
                return stale_cache
            raise
            
        except Exception as e:
            ai_logger.error(
                "Failed to generate smart insights",
                source_system_id=source_system_id,
                error=str(e)
            )
            raise

    
    def generate_forecast(
        self,
        source_system_id: str,
        historical_days: int = 60
    ) -> Dict:
        """
        Generate 7-day forecast of file arrivals.
        
        Args:
            source_system_id: Source system identifier
            historical_days: Number of historical days to analyze (max 90)
            
        Returns:
            Dictionary with daily predictions and confidence levels
        """
        ai_logger.info(
            "Generating forecast",
            source_system_id=source_system_id,
            historical_days=historical_days
        )
        
        # Enforce limits
        historical_days = min(max(historical_days, 30), 90)
        
        # Generate cache key
        cache_key = self.cache_manager.generate_cache_key(
            "forecast",
            source_system_id,
            historical_days=historical_days
        )
        
        # Check cache
        cached = self.cache_manager.get_cached_insight(cache_key)
        if cached:
            ai_logger.info("Returning cached forecast", cache_key=cache_key)
            return cached
        
        try:
            # Get historical patterns
            historical_data = self.data_aggregator.get_historical_patterns(
                source_system_id,
                historical_days
            )
            
            # Build prompt
            prompt = self.prompt_builder.build_forecast_prompt(historical_data)
            
            # Call AI service with retry
            response_text = self._invoke_with_retry(prompt)
            
            # Parse response
            forecast = self._parse_forecast_response(
                response_text,
                source_system_id,
                historical_data
            )
            
            # Cache response
            ttl = self.cache_manager.get_ttl_for_insight_type("forecast")
            self.cache_manager.set_cached_insight(cache_key, forecast, ttl)
            
            ai_logger.info(
                "Forecast generated successfully",
                source_system_id=source_system_id
            )
            
            return forecast
            
        except (BedrockTimeoutError, BedrockUnavailableError) as e:
            # Try to return stale cache on service errors
            ai_logger.warning(
                "AI service error, attempting stale cache fallback",
                error=str(e)
            )
            stale_cache = self.cache_manager.get_cached_insight(
                cache_key,
                ignore_ttl=True
            )
            if stale_cache:
                ai_logger.info("Returning stale cached forecast")
                return stale_cache
            raise
            
        except Exception as e:
            ai_logger.error(
                "Failed to generate forecast",
                source_system_id=source_system_id,
                error=str(e)
            )
            raise
    
    def generate_root_cause_analysis(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Analyze SLA violations and suggest root causes.
        
        Args:
            source_system_id: Source system identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary with causes, correlations, remediation actions
        """
        ai_logger.info(
            "Generating root cause analysis",
            source_system_id=source_system_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Generate cache key
        cache_key = self.cache_manager.generate_cache_key(
            "root_cause",
            source_system_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Check cache
        cached = self.cache_manager.get_cached_insight(cache_key)
        if cached:
            ai_logger.info("Returning cached root cause analysis", cache_key=cache_key)
            return cached
        
        try:
            # Get violation data
            violations = self.data_aggregator.get_sla_violation_summary(
                source_system_id,
                start_date,
                end_date
            )
            
            # Get file arrival context
            context = self.data_aggregator.get_file_arrival_summary(
                source_system_id,
                start_date,
                end_date
            )
            
            # Build prompt
            prompt = self.prompt_builder.build_root_cause_prompt(violations, context)
            
            # Call AI service with retry
            response_text = self._invoke_with_retry(prompt)
            
            # Parse response
            root_cause = self._parse_root_cause_response(
                response_text,
                source_system_id,
                start_date,
                end_date,
                violations['total_violations']
            )
            
            # Cache response
            ttl = self.cache_manager.get_ttl_for_insight_type("root_cause")
            self.cache_manager.set_cached_insight(cache_key, root_cause, ttl)
            
            ai_logger.info(
                "Root cause analysis generated successfully",
                source_system_id=source_system_id
            )
            
            return root_cause
            
        except (BedrockTimeoutError, BedrockUnavailableError) as e:
            # Try to return stale cache on service errors
            ai_logger.warning(
                "AI service error, attempting stale cache fallback",
                error=str(e)
            )
            stale_cache = self.cache_manager.get_cached_insight(
                cache_key,
                ignore_ttl=True
            )
            if stale_cache:
                ai_logger.info("Returning stale cached root cause analysis")
                return stale_cache
            raise
            
        except Exception as e:
            ai_logger.error(
                "Failed to generate root cause analysis",
                source_system_id=source_system_id,
                error=str(e)
            )
            raise
    
    def _invoke_with_retry(self, prompt: str, max_retries: int = 1) -> str:
        """
        Invoke Bedrock with retry logic for timeouts.
        
        Args:
            prompt: Prompt to send
            max_retries: Maximum number of retries
            
        Returns:
            Generated text response
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.bedrock_client.invoke_model(prompt)
            except BedrockTimeoutError as e:
                last_error = e
                if attempt < max_retries:
                    ai_logger.warning(
                        "Bedrock timeout, retrying",
                        attempt=attempt + 1,
                        max_retries=max_retries
                    )
                    continue
                raise
            except BedrockError:
                # Don't retry other errors
                raise
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise BedrockError("Unexpected error in retry logic")
    
    def _parse_insights_response(
        self,
        response_text: str,
        source_system_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Parse AI response for insights.
        
        Args:
            response_text: Raw AI response
            source_system_id: Source system identifier
            start_date: Start date
            end_date: End date
            
        Returns:
            Structured insights dictionary
        """
        # Extract sections from response
        sections = {
            "summary": "",
            "trends": [],
            "anomalies": [],
            "recommendations": []
        }
        
        current_section = None
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if line.upper().startswith("SUMMARY:"):
                current_section = "summary"
                line = line[8:].strip()
            elif line.upper().startswith("TRENDS:"):
                current_section = "trends"
                continue
            elif line.upper().startswith("ANOMALIES:"):
                current_section = "anomalies"
                continue
            elif line.upper().startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
                continue
            
            # Add content to current section
            if current_section == "summary" and line:
                sections["summary"] += line + " "
            elif current_section == "trends" and line.startswith("-"):
                sections["trends"].append({
                    "type": "trend",
                    "description": line[1:].strip(),
                    "confidence": "medium"
                })
            elif current_section == "anomalies" and line.startswith("-"):
                sections["anomalies"].append({
                    "description": line[1:].strip(),
                    "severity": "medium"
                })
            elif current_section == "recommendations" and (line.startswith("-") or line[0].isdigit()):
                # Remove leading dash or number
                rec = line.lstrip("-0123456789. ").strip()
                if rec:
                    sections["recommendations"].append(rec)
        
        return {
            "source_system_id": source_system_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "insights": sections["summary"].strip(),
            "trends": sections["trends"],
            "anomalies": sections["anomalies"],
            "recommendations": sections["recommendations"],
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "cached": False
        }
    
    def _parse_forecast_response(
        self,
        response_text: str,
        source_system_id: str,
        historical_data: Dict
    ) -> Dict:
        """
        Parse AI response for forecast.
        
        Args:
            response_text: Raw AI response
            source_system_id: Source system identifier
            historical_data: Historical data used for forecast
            
        Returns:
            Structured forecast dictionary
        """
        # Try to extract JSON from response
        try:
            # Find JSON block
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                predictions = parsed.get("predictions", [])
                reasoning = parsed.get("reasoning", "")
            else:
                # Fallback: create simple predictions
                predictions = self._create_fallback_predictions(historical_data)
                reasoning = "Generated from historical averages"
        except json.JSONDecodeError:
            # Fallback: create simple predictions
            predictions = self._create_fallback_predictions(historical_data)
            reasoning = "Generated from historical averages"
        
        # Ensure we have exactly 7 predictions
        if len(predictions) < 7:
            predictions = self._create_fallback_predictions(historical_data)
        
        # Format predictions with confidence ranges
        formatted_predictions = []
        for i, pred in enumerate(predictions[:7]):
            pred_date = date.today() + timedelta(days=i + 1)
            count = pred.get("count", 0)
            confidence = pred.get("confidence", "medium")
            
            # Calculate confidence range (±20% for high, ±30% for medium, ±40% for low)
            range_pct = {"high": 0.2, "medium": 0.3, "low": 0.4}.get(confidence, 0.3)
            min_count = max(0, int(count * (1 - range_pct)))
            max_count = int(count * (1 + range_pct))
            
            formatted_predictions.append({
                "date": pred_date.isoformat(),
                "predicted_count": count,
                "confidence_level": confidence,
                "confidence_range": {
                    "min": min_count,
                    "max": max_count
                }
            })
        
        return {
            "source_system_id": source_system_id,
            "forecast_generated_at": datetime.utcnow().isoformat() + "Z",
            "historical_period": historical_data["historical_period"],
            "predictions": formatted_predictions,
            "patterns_identified": [reasoning] if reasoning else [],
            "cached": False
        }
    
    def _parse_root_cause_response(
        self,
        response_text: str,
        source_system_id: str,
        start_date: date,
        end_date: date,
        violations_count: int
    ) -> Dict:
        """
        Parse AI response for root cause analysis.
        
        Args:
            response_text: Raw AI response
            source_system_id: Source system identifier
            start_date: Start date
            end_date: End date
            violations_count: Number of violations analyzed
            
        Returns:
            Structured root cause dictionary
        """
        sections = {
            "root_causes": [],
            "correlations": [],
            "remediation_actions": []
        }
        
        current_section = None
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if "ROOT CAUSE" in line.upper():
                current_section = "root_causes"
                continue
            elif "CORRELATION" in line.upper():
                current_section = "correlations"
                continue
            elif "REMEDIATION" in line.upper() or "ACTION" in line.upper():
                current_section = "remediation_actions"
                continue
            elif "STATUS:" in line.upper():
                # Healthy status case
                continue
            elif "RECOMMENDATION" in line.upper() and violations_count == 0:
                current_section = "remediation_actions"
                continue
            
            # Add content to current section
            if current_section == "root_causes" and line.startswith("-"):
                cause_text = line[1:].strip()
                sections["root_causes"].append({
                    "cause": cause_text.split(":")[0].strip() if ":" in cause_text else cause_text,
                    "description": cause_text,
                    "confidence": "medium"
                })
            elif current_section == "correlations" and line.startswith("-"):
                sections["correlations"].append({
                    "pattern": line[1:].strip(),
                    "strength": "moderate"
                })
            elif current_section == "remediation_actions" and (line.startswith("-") or line[0].isdigit()):
                action = line.lstrip("-0123456789. ").strip()
                if action:
                    sections["remediation_actions"].append(action)
        
        return {
            "source_system_id": source_system_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "violations_analyzed": violations_count,
            "root_causes": sections["root_causes"],
            "correlations": sections["correlations"],
            "remediation_actions": sections["remediation_actions"],
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "cached": False
        }
    
    def _create_fallback_predictions(self, historical_data: Dict) -> list:
        """
        Create simple predictions from historical averages.
        
        Args:
            historical_data: Historical data
            
        Returns:
            List of 7 predictions
        """
        avg_count = historical_data["statistics"]["avg_count"]
        dow_avg = historical_data.get("day_of_week_averages", {})
        
        predictions = []
        for i in range(7):
            pred_date = date.today() + timedelta(days=i + 1)
            dow = pred_date.weekday()  # 0=Monday, 6=Sunday
            
            # Adjust for SQLite day of week (0=Sunday)
            sqlite_dow = (dow + 1) % 7
            
            # Use day-of-week average if available, otherwise overall average
            count = int(dow_avg.get(sqlite_dow, avg_count))
            
            predictions.append({
                "date": pred_date.isoformat(),
                "count": count,
                "confidence": "medium"
            })
        
        return predictions
