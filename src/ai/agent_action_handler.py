"""Action handler for Bedrock Agent tool execution."""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import text

from src.ai.anomaly_detector import BedrockAnomalyDetector
from src.ai.sql_query_generator import SQLQueryGenerator
from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import SourceSystemModel

logger = get_logger(__name__)


class AgentActionHandler:
    """Handles action execution for Bedrock Agent."""
    
    def __init__(self):
        """Initialize action handler."""
        self.sql_generator = SQLQueryGenerator()
        self.anomaly_detector = BedrockAnomalyDetector()
    
    def handle_action(self, action_group: str, api_path: str, parameters: List[Dict]) -> Dict[str, Any]:
        """
        Handle action execution from Bedrock Agent.
        
        Args:
            action_group: Name of the action group
            api_path: API path being called
            parameters: List of parameter dicts with name and value
            
        Returns:
            Dictionary with action response
        """
        # Convert parameters list to dict
        params = {p['name']: p['value'] for p in parameters}
        
        logger.info(
            "Handling agent action",
            action_group=action_group,
            api_path=api_path,
            params=params
        )
        
        try:
            # Route to appropriate handler
            if api_path == '/system-health':
                return self._get_system_health(params)
            elif api_path == '/violations':
                return self._get_violations(params)
            elif api_path == '/trends':
                return self._get_trends(params)
            elif api_path == '/compare-systems':
                return self._compare_systems(params)
            elif api_path == '/insights':
                return self._get_insights(params)
            elif api_path == '/forecast':
                return self._get_forecast(params)
            elif api_path == '/root-cause':
                return self._analyze_root_cause(params)
            elif api_path == '/all-systems':
                return self._query_all_systems(params)
            else:
                return {'error': f'Unknown API path: {api_path}'}
                
        except Exception as e:
            logger.error(f"Error handling action: {e}")
            return {'error': str(e)}
    
    def _get_system_health(self, params: Dict) -> Dict:
        """Get system health status."""
        system_id = params.get('system_id')
        days = int(params.get('days', 7))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sql, sql_params = self.sql_generator.generateHealthQuery(
            system_id,
            (start_date, end_date)
        )
        
        result = self._execute_query(sql, sql_params)
        
        return {
            'system_id': system_id,
            'period_days': days,
            'data': result
        }
    
    def _get_violations(self, params: Dict) -> Dict:
        """Get SLA violations."""
        system_ids_str = params.get('system_ids', '')
        system_ids = [s.strip() for s in system_ids_str.split(',') if s.strip()]
        days = int(params.get('days', 7))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        filters = {
            'system_ids': system_ids if system_ids else None,
            'date_range': (start_date, end_date)
        }
        
        sql, sql_params = self.sql_generator.generateViolationsQuery(filters)
        result = self._execute_query(sql, sql_params)
        
        return {
            'systems': system_ids or 'all',
            'period_days': days,
            'violation_count': len(result),
            'violations': result
        }
    
    def _get_trends(self, params: Dict) -> Dict:
        """Get file arrival trends."""
        system_id = params.get('system_id')
        days = int(params.get('days', 14))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sql, sql_params = self.sql_generator.generateTrendsQuery(
            system_id,
            (start_date, end_date),
            granularity='daily'
        )
        
        result = self._execute_query(sql, sql_params)
        
        return {
            'system_id': system_id,
            'period_days': days,
            'data_points': len(result),
            'trends': result
        }
    
    def _compare_systems(self, params: Dict) -> Dict:
        """Compare multiple systems."""
        system_ids_str = params.get('system_ids', '')
        system_ids = [s.strip() for s in system_ids_str.split(',') if s.strip()]
        
        if len(system_ids) < 2:
            return {'error': 'Need at least 2 systems to compare'}
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        sql, sql_params = self.sql_generator.generateComparisonQuery(
            system_ids,
            (start_date, end_date)
        )
        
        result = self._execute_query(sql, sql_params)
        
        return {
            'systems_compared': system_ids,
            'comparison_data': result
        }
    
    def _get_insights(self, params: Dict) -> Dict:
        """Generate AI insights."""
        system_id = params.get('system_id')
        days = int(params.get('days', 30))
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Use existing AI insights endpoint
        try:
            insights = self.anomaly_detector.generate_insights(
                system_id,
                start_date,
                end_date
            )
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                'system_id': system_id,
                'insights': f'Unable to generate insights at this time',
                'error': str(e)
            }
    
    def _get_forecast(self, params: Dict) -> Dict:
        """Get forecast predictions."""
        system_id = params.get('system_id')
        
        # Return placeholder - forecast feature can be added later
        return {
            'system_id': system_id,
            'forecast': 'Forecast feature coming soon',
            'message': 'Historical data shows consistent patterns'
        }
    
    def _analyze_root_cause(self, params: Dict) -> Dict:
        """Analyze root cause of violations."""
        system_id = params.get('system_id')
        days = int(params.get('days', 7))
        
        # Get violations first
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        filters = {
            'system_ids': [system_id],
            'date_range': (start_date, end_date)
        }
        
        sql, sql_params = self.sql_generator.generateViolationsQuery(filters)
        violations = self._execute_query(sql, sql_params)
        
        if not violations:
            return {
                'system_id': system_id,
                'analysis': 'No violations found in the specified period',
                'violations_count': 0
            }
        
        # Simple root cause analysis
        violation_types = {}
        for v in violations:
            vtype = v.get('violation_type', 'unknown')
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        return {
            'system_id': system_id,
            'period_days': days,
            'violations_count': len(violations),
            'violation_types': violation_types,
            'analysis': f'Found {len(violations)} violations. Most common type: {max(violation_types, key=violation_types.get) if violation_types else "N/A"}'
        }
    
    def _query_all_systems(self, params: Dict) -> Dict:
        """Get overview of all systems."""
        with get_db_session() as session:
            systems = session.query(SourceSystemModel).filter_by(is_active=True).all()
            
            result = []
            for system in systems:
                result.append({
                    'id': system.id,
                    'name': system.name,
                    'is_active': system.is_active,
                    'description': system.description
                })
            
            return {
                'total_systems': len(result),
                'systems': result
            }
    
    def _execute_query(self, sql: str, params: Dict) -> List[Dict]:
        """Execute SQL query and return results."""
        with get_db_session() as session:
            result = session.execute(text(sql), params)
            rows = result.fetchall()
            
            # Convert to list of dicts
            if rows:
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            return []


# Global instance
_action_handler = None


def get_action_handler() -> AgentActionHandler:
    """Get or create global action handler instance."""
    global _action_handler
    if _action_handler is None:
        _action_handler = AgentActionHandler()
    return _action_handler
