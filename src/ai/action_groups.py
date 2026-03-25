"""Action groups for Bedrock Agent

These functions can be called by the Bedrock Agent to query the file monitoring system.
"""

import json
from datetime import date, timedelta
from typing import Dict, List, Optional

from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import FileArrivalModel, SourceSystemModel
from src.sla.calculator import ScoreCalculator
from src.sla.tracker import ViolationTracker
from src.analytics.trend_analyzer import TrendAnalyzer

logger = get_logger(__name__)


class ActionGroupHandler:
    """
    Handler for Bedrock Agent action groups.
    
    Each method is an action that the agent can invoke.
    """
    
    @staticmethod
    def get_source_systems(active_only: bool = True) -> Dict:
        """
        Action: Get list of source systems.
        
        Args:
            active_only: Return only active systems
            
        Returns:
            Dictionary with systems list
        """
        logger.info("Action: get_source_systems", active_only=active_only)
        
        try:
            with get_db_session() as session:
                query = session.query(SourceSystemModel)
                
                if active_only:
                    query = query.filter_by(is_active=True)
                
                systems = query.all()
                
                result = []
                for sys in systems:
                    _ = (sys.id, sys.name, sys.directory_path, sys.is_active)
                    session.expunge(sys)
                    
                    result.append({
                        "id": sys.id,
                        "name": sys.name,
                        "directory_path": sys.directory_path,
                        "is_active": sys.is_active,
                    })
                
                return {
                    "systems": result,
                    "count": len(result),
                }
        except Exception as e:
            logger.error("Action failed", action="get_source_systems", error=str(e))
            return {"error": str(e)}
    
    @staticmethod
    def get_sla_violations(
        source_system_id: Optional[str] = None,
        days: int = 7,
        severity: Optional[str] = None,
    ) -> Dict:
        """
        Action: Get SLA violations.
        
        Args:
            source_system_id: Filter by system (optional)
            days: Number of days to look back
            severity: Filter by severity (optional)
            
        Returns:
            Dictionary with violations
        """
        logger.info(
            "Action: get_sla_violations",
            source_system_id=source_system_id,
            days=days,
            severity=severity,
        )
        
        try:
            tracker = ViolationTracker()
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            violations = tracker.get_violations(
                source_system_id=source_system_id,
                start_date=start_date,
                end_date=end_date,
                severity=severity,
                limit=100,
            )
            
            result = [
                {
                    "id": v.id,
                    "system": v.source_system_id,
                    "date": v.violation_date.isoformat(),
                    "type": v.violation_type,
                    "severity": v.severity,
                    "expected": v.expected_value,
                    "actual": v.actual_value,
                }
                for v in violations
            ]
            
            return {
                "violations": result,
                "count": len(result),
                "period": f"{start_date} to {end_date}",
            }
        except Exception as e:
            logger.error("Action failed", action="get_sla_violations", error=str(e))
            return {"error": str(e)}
    
    @staticmethod
    def get_sla_scores(
        source_system_id: str,
        days: int = 30,
    ) -> Dict:
        """
        Action: Get SLA scores for a system.
        
        Args:
            source_system_id: System to get scores for
            days: Number of days
            
        Returns:
            Dictionary with scores
        """
        logger.info(
            "Action: get_sla_scores",
            source_system_id=source_system_id,
            days=days,
        )
        
        try:
            calculator = ScoreCalculator()
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            scores = calculator.calculate_score_range(
                source_system_id, start_date, end_date
            )
            
            # Calculate average
            avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0
            
            return {
                "system": source_system_id,
                "period": f"{start_date} to {end_date}",
                "scores": scores,
                "average_score": round(avg_score, 2),
                "days_analyzed": len(scores),
            }
        except Exception as e:
            logger.error("Action failed", action="get_sla_scores", error=str(e))
            return {"error": str(e)}
    
    @staticmethod
    def get_file_trends(
        source_system_id: str,
        days: int = 30,
    ) -> Dict:
        """
        Action: Get file arrival trends.
        
        Args:
            source_system_id: System to analyze
            days: Number of days
            
        Returns:
            Dictionary with trend data
        """
        logger.info(
            "Action: get_file_trends",
            source_system_id=source_system_id,
            days=days,
        )
        
        try:
            analyzer = TrendAnalyzer()
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            daily_counts = analyzer.get_daily_counts(
                source_system_id, start_date, end_date
            )
            
            result = [
                {
                    "date": dc.arrival_date.isoformat(),
                    "count": dc.file_count,
                    "total_size_mb": round(dc.total_size_bytes / (1024 * 1024), 2),
                }
                for dc in daily_counts
            ]
            
            # Calculate statistics
            counts = [dc.file_count for dc in daily_counts]
            avg_count = sum(counts) / len(counts) if counts else 0
            max_count = max(counts) if counts else 0
            min_count = min(counts) if counts else 0
            
            return {
                "system": source_system_id,
                "period": f"{start_date} to {end_date}",
                "daily_counts": result,
                "statistics": {
                    "average": round(avg_count, 2),
                    "maximum": max_count,
                    "minimum": min_count,
                    "total_days": len(result),
                },
            }
        except Exception as e:
            logger.error("Action failed", action="get_file_trends", error=str(e))
            return {"error": str(e)}
    
    @staticmethod
    def get_file_count_today(
        source_system_id: Optional[str] = None,
    ) -> Dict:
        """
        Action: Get file count for today.
        
        Args:
            source_system_id: Filter by system (optional)
            
        Returns:
            Dictionary with today's file count
        """
        logger.info(
            "Action: get_file_count_today",
            source_system_id=source_system_id,
        )
        
        try:
            from datetime import datetime as dt
            
            with get_db_session() as session:
                today_start = dt.combine(date.today(), dt.min.time())
                
                query = session.query(FileArrivalModel).filter(
                    FileArrivalModel.arrival_timestamp >= today_start
                )
                
                if source_system_id:
                    query = query.filter_by(source_system_id=source_system_id)
                
                count = query.count()
                
                # Get breakdown by system if no specific system requested
                if not source_system_id:
                    systems = session.query(SourceSystemModel).filter_by(
                        is_active=True
                    ).all()
                    
                    breakdown = []
                    for sys in systems:
                        _ = (sys.id, sys.name)
                        session.expunge(sys)
                        
                        sys_count = session.query(FileArrivalModel).filter(
                            FileArrivalModel.source_system_id == sys.id,
                            FileArrivalModel.arrival_timestamp >= today_start
                        ).count()
                        
                        breakdown.append({
                            "system_id": sys.id,
                            "system_name": sys.name,
                            "count": sys_count,
                        })
                    
                    return {
                        "date": date.today().isoformat(),
                        "total_count": count,
                        "breakdown": breakdown,
                    }
                else:
                    return {
                        "date": date.today().isoformat(),
                        "system": source_system_id,
                        "count": count,
                    }
        except Exception as e:
            logger.error("Action failed", action="get_file_count_today", error=str(e))
            return {"error": str(e)}
    
    @staticmethod
    def get_system_health_summary() -> Dict:
        """
        Action: Get overall system health summary.
        
        Returns:
            Dictionary with health metrics for all systems
        """
        logger.info("Action: get_system_health_summary")
        
        try:
            calculator = ScoreCalculator()
            tracker = ViolationTracker()
            
            with get_db_session() as session:
                systems = session.query(SourceSystemModel).filter_by(
                    is_active=True
                ).all()
                
                summary = []
                for sys in systems:
                    _ = (sys.id, sys.name)
                    session.expunge(sys)
                    
                    # Get today's score
                    score = calculator.calculate_daily_score(sys.id, date.today())
                    
                    # Get violations this week
                    week_ago = date.today() - timedelta(days=7)
                    violations = tracker.get_violation_count(
                        sys.id, start_date=week_ago
                    )
                    
                    # Determine health status
                    if score >= 90 and violations == 0:
                        status = "Healthy"
                    elif score >= 70:
                        status = "Warning"
                    else:
                        status = "Critical"
                    
                    summary.append({
                        "system_id": sys.id,
                        "system_name": sys.name,
                        "sla_score": round(score, 2),
                        "violations_this_week": violations,
                        "status": status,
                    })
                
                # Overall statistics
                avg_score = sum(s["sla_score"] for s in summary) / len(summary) if summary else 0
                total_violations = sum(s["violations_this_week"] for s in summary)
                
                return {
                    "date": date.today().isoformat(),
                    "systems": summary,
                    "overall": {
                        "average_sla_score": round(avg_score, 2),
                        "total_violations_this_week": total_violations,
                        "systems_healthy": len([s for s in summary if s["status"] == "Healthy"]),
                        "systems_warning": len([s for s in summary if s["status"] == "Warning"]),
                        "systems_critical": len([s for s in summary if s["status"] == "Critical"]),
                    },
                }
        except Exception as e:
            logger.error("Action failed", action="get_system_health_summary", error=str(e))
            return {"error": str(e)}
    
    @staticmethod
    def compare_systems(
        system_ids: List[str],
        days: int = 30,
    ) -> Dict:
        """
        Action: Compare multiple systems.
        
        Args:
            system_ids: List of system IDs to compare
            days: Number of days to analyze
            
        Returns:
            Dictionary with comparison data
        """
        logger.info(
            "Action: compare_systems",
            system_ids=system_ids,
            days=days,
        )
        
        try:
            analyzer = TrendAnalyzer()
            calculator = ScoreCalculator()
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            comparison = []
            for system_id in system_ids:
                # Get daily counts
                daily_counts = analyzer.get_daily_counts(
                    system_id, start_date, end_date
                )
                
                counts = [dc.file_count for dc in daily_counts]
                avg_count = sum(counts) / len(counts) if counts else 0
                
                # Get average SLA score
                avg_score = calculator.get_average_score(
                    system_id, start_date, end_date
                )
                
                comparison.append({
                    "system_id": system_id,
                    "avg_daily_files": round(avg_count, 2),
                    "avg_sla_score": round(avg_score, 2),
                    "total_files": sum(counts),
                })
            
            return {
                "period": f"{start_date} to {end_date}",
                "systems_compared": len(comparison),
                "comparison": comparison,
            }
        except Exception as e:
            logger.error("Action failed", action="compare_systems", error=str(e))
            return {"error": str(e)}


# Lambda handler for Bedrock Agent action group
def lambda_handler(event, context):
    """
    AWS Lambda handler for Bedrock Agent action group.
    
    This function is called by Bedrock Agent when it needs to execute an action.
    
    Args:
        event: Lambda event from Bedrock Agent
        context: Lambda context
        
    Returns:
        Response in Bedrock Agent format
    """
    logger.info("Lambda handler invoked", event=event)
    
    try:
        # Extract action and parameters
        action_group = event.get('actionGroup', '')
        action = event.get('function', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters to dict
        params = {p['name']: p['value'] for p in parameters}
        
        # Route to appropriate action
        handler = ActionGroupHandler()
        
        if action == 'get_source_systems':
            result = handler.get_source_systems(**params)
        elif action == 'get_sla_violations':
            result = handler.get_sla_violations(**params)
        elif action == 'get_sla_scores':
            result = handler.get_sla_scores(**params)
        elif action == 'get_file_trends':
            result = handler.get_file_trends(**params)
        elif action == 'get_file_count_today':
            result = handler.get_file_count_today(**params)
        elif action == 'get_system_health_summary':
            result = handler.get_system_health_summary()
        elif action == 'compare_systems':
            result = handler.compare_systems(**params)
        else:
            result = {"error": f"Unknown action: {action}"}
        
        # Return in Bedrock Agent format
        return {
            'response': {
                'actionGroup': action_group,
                'function': action,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error("Lambda handler error", error=str(e))
        return {
            'response': {
                'actionGroup': event.get('actionGroup', ''),
                'function': event.get('function', ''),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({"error": str(e)})
                        }
                    }
                }
            }
        }
