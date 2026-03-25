"""SLA score calculator for SQLite"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import SLAViolationModel, SLAScoreModel

logger = get_logger(__name__)


class ScoreCalculator:
    """
    Calculates SLA scores based on violations using SQLite.
    
    Stores calculated scores in sla_scores table for caching.
    """
    
    def __init__(self):
        """Initialize score calculator"""
        logger.info("ScoreCalculator initialized")
    
    def calculate_daily_score(
        self,
        source_system_id: str,
        target_date: date,
    ) -> float:
        """
        Calculate SLA score for a specific day.
        
        Args:
            source_system_id: Source system ID
            target_date: Date to calculate score for
            
        Returns:
            Score value (0-100)
        """
        with get_db_session() as session:
            # Query violations for the day
            violations = session.query(SLAViolationModel).filter(
                SLAViolationModel.source_system_id == source_system_id,
                SLAViolationModel.violation_date == target_date,
            ).all()
            
            # Simple scoring: 100 if no violations, decrease by 10 per violation
            # Capped at 0
            score_value = 100.0 - (len(violations) * 10.0)
            score_value = max(0.0, score_value)
            
            logger.debug(
                "Calculated daily score",
                source_system_id=source_system_id,
                date=target_date.isoformat(),
                score=score_value,
                violations=len(violations),
            )
            
            return score_value
    
    def store_daily_score(
        self,
        source_system_id: str,
        target_date: date,
        score: float,
        total_checks: int,
        passed_checks: int,
    ) -> None:
        """
        Store calculated score in database for caching.
        
        Args:
            source_system_id: Source system ID
            target_date: Date of score
            score: Score value (0-100)
            total_checks: Total number of checks
            passed_checks: Number of passed checks
        """
        with get_db_session() as session:
            # Check if score already exists
            existing = session.query(SLAScoreModel).filter(
                SLAScoreModel.source_system_id == source_system_id,
                SLAScoreModel.score_date == target_date,
            ).first()
            
            if existing:
                # Update existing
                existing.score = score
                existing.total_checks = total_checks
                existing.passed_checks = passed_checks
                existing.calculated_at = datetime.utcnow()
            else:
                # Create new
                score_model = SLAScoreModel(
                    source_system_id=source_system_id,
                    score_date=target_date,
                    score=score,
                    total_checks=total_checks,
                    passed_checks=passed_checks,
                )
                session.add(score_model)
            
            session.commit()
            
            logger.debug(
                "Stored daily score",
                source_system_id=source_system_id,
                date=target_date.isoformat(),
                score=score,
            )
    
    def get_stored_score(
        self,
        source_system_id: str,
        target_date: date,
    ) -> Optional[float]:
        """
        Get previously calculated score from cache.
        
        Args:
            source_system_id: Source system ID
            target_date: Date of score
            
        Returns:
            Score value or None if not found
        """
        with get_db_session() as session:
            score_model = session.query(SLAScoreModel).filter(
                SLAScoreModel.source_system_id == source_system_id,
                SLAScoreModel.score_date == target_date,
            ).first()
            
            if score_model:
                return float(score_model.score)
            
            return None
    
    def calculate_and_store_daily_score(
        self,
        source_system_id: str,
        target_date: date,
    ) -> float:
        """
        Calculate daily score and store it in database.
        
        Args:
            source_system_id: Source system ID
            target_date: Date to calculate for
            
        Returns:
            Score value (0-100)
        """
        score = self.calculate_daily_score(source_system_id, target_date)
        
        # Count checks (simplified: 1 check per day)
        total_checks = 1
        passed_checks = 1 if score >= 90.0 else 0
        
        self.store_daily_score(
            source_system_id,
            target_date,
            score,
            total_checks,
            passed_checks,
        )
        
        return score
    
    def calculate_score_range(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True,
    ) -> List[dict]:
        """
        Calculate daily scores for a date range.
        
        Args:
            source_system_id: Source system ID
            start_date: Start date
            end_date: End date
            use_cache: Use cached scores if available
            
        Returns:
            List of score dictionaries
        """
        scores = []
        current_date = start_date
        
        while current_date <= end_date:
            # Try to get from cache first
            if use_cache:
                cached_score = self.get_stored_score(source_system_id, current_date)
                if cached_score is not None:
                    scores.append({
                        "date": current_date.isoformat(),
                        "score": cached_score,
                    })
                    current_date += timedelta(days=1)
                    continue
            
            # Calculate and store
            score = self.calculate_and_store_daily_score(source_system_id, current_date)
            scores.append({
                "date": current_date.isoformat(),
                "score": score,
            })
            
            current_date += timedelta(days=1)
        
        logger.info(
            f"Calculated {len(scores)} daily scores",
            source_system_id=source_system_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        
        return scores
    
    def get_average_score(
        self,
        source_system_id: str,
        start_date: date,
        end_date: date,
    ) -> float:
        """
        Calculate average score for a date range.
        
        Args:
            source_system_id: Source system ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Average score (0-100)
        """
        scores = self.calculate_score_range(source_system_id, start_date, end_date)
        
        if not scores:
            return 100.0
        
        avg_score = sum(s["score"] for s in scores) / len(scores)
        return avg_score
