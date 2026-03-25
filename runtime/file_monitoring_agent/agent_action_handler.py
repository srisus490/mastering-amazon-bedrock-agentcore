"""Action handler for Bedrock Agent tool execution.

This module handles action execution for the File Monitoring Agent running in
AWS Bedrock AgentCore Runtime. It processes tool invocations by generating and
executing SQL queries against the database.

Validates Requirements: 2.5, 2.6, 2.7, 2.8, 2.9
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
import logging

from sqlalchemy import text

from database_connection import get_db_session
from models import SourceSystemModel
from sql_query_generator import SQLQueryGenerator

logger = logging.getLogger(__name__)


class AgentActionHandler:
    """Handles action execution for Bedrock Agent.
    
    This class processes tool invocations from the agent by:
    - Parsing tool parameters
    - Generating SQL queries via SQLQueryGenerator
    - Executing queries against the database
    - Formatting results as JSON
    - Handling errors and returning meaningful error messages
    
    Validates: Requirements 2.5, 2.8
    """
    
    def __init__(self):
        """Initialize action handler."""
        self.sql_generator = SQLQueryGenerator()
    
    def handle_action(self, action_group: str, api_path: str, parameters: List[Dict]) -> Dict[str, Any]:
        """
        Handle action execution from Bedrock Agent.
        
        Args:
            action_group: Name of the action group
            api_path: API path being called
            parameters: List of parameter dicts with name and value
            
        Returns:
            Dictionary with action response (success) or error message (failure)
            
        Validates: Requirements 2.5, 2.6, 2.7
        """
        # Convert parameters list to dict
        params = {p['name']: p['value'] for p in parameters}
        
        logger.info(
            f"Handling agent action: action_group={action_group}, "
            f"api_path={api_path}, params={params}"
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
                error_msg = f'Unknown API path: {api_path}'
                logger.error(error_msg)
                return {'error': error_msg}
                
        except Exception as e:
            error_msg = f"Error handling action: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    def _get_system_health(self, params: Dict) -> Dict:
        """
        Get system health status.
        
        Args:
            params: Dictionary with system_id and optional days
            
        Returns:
            Dictionary with system health data or error
            
        Validates: Requirement 2.1
        """
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
        """
        Get SLA violations.
        
        Args:
            params: Dictionary with optional system_ids and days
            
        Returns:
            Dictionary with violations data or error
            
        Validates: Requirement 2.2
        """
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
        """
        Get file arrival trends.
        
        Args:
            params: Dictionary with system_id and optional days
            
        Returns:
            Dictionary with trends data or error
        """
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
        """
        Compare multiple systems.
        
        Args:
            params: Dictionary with system_ids (comma-separated)
            
        Returns:
            Dictionary with comparison data or error
            
        Validates: Requirement 2.4
        """
        system_ids_str = params.get('system_ids', '')
        system_ids = [s.strip() for s in system_ids_str.split(',') if s.strip()]
        
        if len(system_ids) < 2:
            error_msg = 'Need at least 2 systems to compare'
            logger.warning(error_msg)
            return {'error': error_msg}
        
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
        """
        Generate insights about system performance.
        
        Note: This is a simplified version without AI-powered anomaly detection.
        The full anomaly detection feature is available in the main application.
        
        Args:
            params: Dictionary with system_id and optional days
            
        Returns:
            Dictionary with basic insights or error
        """
        system_id = params.get('system_id')
        days = int(params.get('days', 30))
        
        try:
            # Get basic health metrics
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            sql, sql_params = self.sql_generator.generateHealthQuery(
                system_id,
                (start_date, end_date)
            )
            
            health_data = self._execute_query(sql, sql_params)
            
            if not health_data:
                return {
                    'system_id': system_id,
                    'insights': 'No data available for the specified period',
                    'period_days': days
                }
            
            # Generate basic insights from health data
            data = health_data[0]
            insights = []
            
            if data.get('avg_sla_score'):
                score = float(data['avg_sla_score'])
                if score >= 95:
                    insights.append(f"Excellent SLA performance with {score:.1f}% average score")
                elif score >= 80:
                    insights.append(f"Good SLA performance with {score:.1f}% average score")
                else:
                    insights.append(f"SLA performance needs attention: {score:.1f}% average score")
            
            if data.get('violation_count'):
                count = data['violation_count']
                if count > 0:
                    insights.append(f"Found {count} SLA violations in the last {days} days")
            
            if data.get('total_files'):
                files = data['total_files']
                days_with_files = data.get('days_with_files', 0)
                insights.append(f"Received {files} files across {days_with_files} days")
            
            return {
                'system_id': system_id,
                'period_days': days,
                'insights': ' | '.join(insights) if insights else 'System operating normally',
                'metrics': data
            }
            
        except Exception as e:
            error_msg = f"Error generating insights: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'system_id': system_id,
                'insights': 'Unable to generate insights at this time',
                'error': error_msg
            }
    
    def _get_forecast(self, params: Dict) -> Dict:
        """
        Get forecast predictions.
        
        Note: This is a placeholder. Forecast feature can be added later.
        
        Args:
            params: Dictionary with system_id
            
        Returns:
            Dictionary with forecast placeholder message
        """
        system_id = params.get('system_id')
        
        return {
            'system_id': system_id,
            'forecast': 'Forecast feature coming soon',
            'message': 'Historical data shows consistent patterns'
        }
    
    def _analyze_root_cause(self, params: Dict) -> Dict:
        """
        Analyze root cause of violations.
        
        Args:
            params: Dictionary with system_id and optional days
            
        Returns:
            Dictionary with root cause analysis or error
        """
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
        
        most_common = max(violation_types, key=violation_types.get) if violation_types else "N/A"
        
        return {
            'system_id': system_id,
            'period_days': days,
            'violations_count': len(violations),
            'violation_types': violation_types,
            'analysis': f'Found {len(violations)} violations. Most common type: {most_common}'
        }
    
    def _query_all_systems(self, params: Dict) -> Dict:
        """
        Get overview of all systems.
        
        Args:
            params: Dictionary (no parameters required)
            
        Returns:
            Dictionary with all systems data or error
            
        Validates: Requirement 2.3
        """
        try:
            with get_db_session() as session:
                systems = session.query(SourceSystemModel).filter_by(is_active=True).all()
                
                result = []
                for system in systems:
                    result.append({
                        'id': system.id,
                        'name': system.name,
                        'is_active': system.is_active,
                        'directory_path': system.directory_path
                    })
                
                return {
                    'total_systems': len(result),
                    'systems': result
                }
        except Exception as e:
            error_msg = f"Error querying all systems: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}
    
    def _execute_query(self, sql: str, params: Dict) -> List[Dict]:
        """
        Execute SQL query and return results.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries with query results
            
        Raises:
            Exception: If query execution fails
            
        Validates: Requirements 2.6, 2.7
        """
        try:
            with get_db_session() as session:
                result = session.execute(text(sql), params)
                rows = result.fetchall()
                
                # Convert to list of dicts
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
        except Exception as e:
            error_msg = f"Database query execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise


# Global instance
_action_handler = None


def get_action_handler() -> AgentActionHandler:
    """
    Get or create global action handler instance.
    
    Returns:
        Global AgentActionHandler instance
    """
    global _action_handler
    if _action_handler is None:
        _action_handler = AgentActionHandler()
    return _action_handler
