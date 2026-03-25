"""SQL query generator for converting natural language queries to SQL."""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.core.logging import get_logger

logger = get_logger(__name__)


class SQLQueryGenerator:
    """Generates safe, parameterized SQL queries from parsed intents."""
    
    # Maximum rows to return
    MAX_ROWS = 1000
    
    # Query timeout in seconds
    QUERY_TIMEOUT = 5
    
    def __init__(self):
        """Initialize the SQL query generator."""
        pass
    
    def generateHealthQuery(
        self,
        system_id: str,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Tuple[str, Dict]:
        """
        Generate SQL query for system health check.
        
        Args:
            system_id: Source system identifier
            date_range: Optional date range tuple (start, end)
            
        Returns:
            Tuple of (SQL query string, parameters dict)
        """
        if not date_range:
            # Default to last 7 days
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            date_range = (start_date, end_date)
        
        query = """
        SELECT 
            ss.id as system_id,
            ss.name as system_name,
            ss.is_active,
            COUNT(DISTINCT DATE(fa.arrival_timestamp)) as days_with_files,
            COUNT(fa.id) as total_files,
            AVG(scores.score) as avg_sla_score,
            COUNT(DISTINCT v.id) as violation_count
        FROM source_systems ss
        LEFT JOIN file_arrivals fa ON ss.id = fa.source_system_id 
            AND fa.arrival_timestamp >= :start_date 
            AND fa.arrival_timestamp <= :end_date
        LEFT JOIN sla_scores scores ON ss.id = scores.source_system_id
            AND scores.score_date >= DATE(:start_date)
            AND scores.score_date <= DATE(:end_date)
        LEFT JOIN sla_violations v ON ss.id = v.source_system_id
            AND v.violation_date >= DATE(:start_date)
            AND v.violation_date <= DATE(:end_date)
        WHERE ss.id = :system_id
        GROUP BY ss.id, ss.name, ss.is_active
        LIMIT :limit
        """
        
        params = {
            'system_id': system_id,
            'start_date': date_range[0].isoformat(),
            'end_date': date_range[1].isoformat(),
            'limit': self.MAX_ROWS
        }
        
        return query.strip(), params
    
    def generateViolationsQuery(
        self,
        filters: Dict
    ) -> Tuple[str, Dict]:
        """
        Generate SQL query for SLA violations.
        
        Args:
            filters: Dictionary with optional keys:
                - system_ids: List of system IDs
                - date_range: Tuple of (start, end) dates
                - severity: Severity level filter
                
        Returns:
            Tuple of (SQL query string, parameters dict)
        """
        query_parts = [
            """
            SELECT 
                v.id,
                v.source_system_id,
                ss.name as system_name,
                v.violation_date,
                v.violation_type,
                v.expected_value,
                v.actual_value,
                v.severity,
                v.created_at
            FROM sla_violations v
            JOIN source_systems ss ON v.source_system_id = ss.id
            WHERE 1=1
            """
        ]
        
        params = {}
        
        # Add system filter
        if filters.get('system_ids'):
            system_ids = filters['system_ids']
            if len(system_ids) == 1:
                query_parts.append("AND v.source_system_id = :system_id")
                params['system_id'] = system_ids[0]
            else:
                placeholders = ', '.join(f':system_id_{i}' for i in range(len(system_ids)))
                query_parts.append(f"AND v.source_system_id IN ({placeholders})")
                for i, sys_id in enumerate(system_ids):
                    params[f'system_id_{i}'] = sys_id
        
        # Add date range filter
        if filters.get('date_range'):
            start_date, end_date = filters['date_range']
            query_parts.append("AND v.violation_date >= DATE(:start_date)")
            query_parts.append("AND v.violation_date <= DATE(:end_date)")
            params['start_date'] = start_date.date().isoformat()
            params['end_date'] = end_date.date().isoformat()
        
        # Add severity filter
        if filters.get('severity'):
            query_parts.append("AND v.severity = :severity")
            params['severity'] = filters['severity']
        
        # Add ordering and limit
        query_parts.append("ORDER BY v.violation_date DESC, v.created_at DESC")
        query_parts.append("LIMIT :limit")
        params['limit'] = self.MAX_ROWS
        
        query = '\n'.join(query_parts)
        return query.strip(), params
    
    def generateTrendsQuery(
        self,
        system_id: str,
        date_range: Tuple[datetime, datetime],
        granularity: str = 'daily'
    ) -> Tuple[str, Dict]:
        """
        Generate SQL query for trend analysis.
        
        Args:
            system_id: Source system identifier
            date_range: Tuple of (start, end) dates
            granularity: 'daily' or 'hourly'
            
        Returns:
            Tuple of (SQL query string, parameters dict)
        """
        if granularity == 'hourly':
            date_format = "strftime('%Y-%m-%d %H:00:00', fa.arrival_timestamp)"
            group_by = "date_hour"
        else:
            date_format = "DATE(fa.arrival_timestamp)"
            group_by = "date_day"
        
        query = f"""
        SELECT 
            {date_format} as period,
            COUNT(fa.id) as file_count,
            AVG(fa.file_size_bytes) as avg_file_size,
            MIN(fa.arrival_timestamp) as first_arrival,
            MAX(fa.arrival_timestamp) as last_arrival
        FROM file_arrivals fa
        WHERE fa.source_system_id = :system_id
            AND fa.arrival_timestamp >= :start_date
            AND fa.arrival_timestamp <= :end_date
        GROUP BY {group_by}
        ORDER BY period ASC
        LIMIT :limit
        """
        
        params = {
            'system_id': system_id,
            'start_date': date_range[0].isoformat(),
            'end_date': date_range[1].isoformat(),
            'limit': self.MAX_ROWS
        }
        
        return query.strip(), params
    
    def generateComparisonQuery(
        self,
        system_ids: List[str],
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Tuple[str, Dict]:
        """
        Generate SQL query for system comparison.
        
        Args:
            system_ids: List of system IDs to compare
            date_range: Optional date range tuple (start, end)
            
        Returns:
            Tuple of (SQL query string, parameters dict)
        """
        if not date_range:
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            date_range = (start_date, end_date)
        
        # Build IN clause for system IDs
        placeholders = ', '.join(f':system_id_{i}' for i in range(len(system_ids)))
        
        query = f"""
        SELECT 
            ss.id as system_id,
            ss.name as system_name,
            COUNT(DISTINCT DATE(fa.arrival_timestamp)) as days_with_files,
            COUNT(fa.id) as total_files,
            AVG(fa.file_size_bytes) as avg_file_size,
            AVG(scores.score) as avg_sla_score,
            COUNT(DISTINCT v.id) as violation_count
        FROM source_systems ss
        LEFT JOIN file_arrivals fa ON ss.id = fa.source_system_id 
            AND fa.arrival_timestamp >= :start_date 
            AND fa.arrival_timestamp <= :end_date
        LEFT JOIN sla_scores scores ON ss.id = scores.source_system_id
            AND scores.score_date >= DATE(:start_date)
            AND scores.score_date <= DATE(:end_date)
        LEFT JOIN sla_violations v ON ss.id = v.source_system_id
            AND v.violation_date >= DATE(:start_date)
            AND v.violation_date <= DATE(:end_date)
        WHERE ss.id IN ({placeholders})
        GROUP BY ss.id, ss.name
        ORDER BY ss.name
        LIMIT :limit
        """
        
        params = {
            'start_date': date_range[0].isoformat(),
            'end_date': date_range[1].isoformat(),
            'limit': self.MAX_ROWS
        }
        
        for i, sys_id in enumerate(system_ids):
            params[f'system_id_{i}'] = sys_id
        
        return query.strip(), params
    
    def validateQuery(self, sql: str) -> bool:
        """
        Validate that a SQL query is safe to execute.
        
        Args:
            sql: SQL query string
            
        Returns:
            True if query is safe, False otherwise
        """
        sql_upper = sql.upper().strip()
        
        # Must be a SELECT query
        if not sql_upper.startswith('SELECT'):
            logger.warning("Query validation failed: Not a SELECT query")
            return False
        
        # Must not contain dangerous keywords
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER',
            'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                logger.warning(f"Query validation failed: Contains dangerous keyword '{keyword}'")
                return False
        
        # Must have a LIMIT clause
        if 'LIMIT' not in sql_upper:
            logger.warning("Query validation failed: Missing LIMIT clause")
            return False
        
        return True
    
    def isExpensiveQuery(
        self,
        date_range: Optional[Tuple[datetime, datetime]],
        system_count: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if a query would be expensive to execute.
        
        Args:
            date_range: Date range for the query
            system_count: Number of systems being queried
            
        Returns:
            Tuple of (is_expensive, suggestion)
        """
        if not date_range:
            return False, None
        
        start_date, end_date = date_range
        days = (end_date - start_date).days
        
        # Large date range
        if days > 90:
            return True, "Consider narrowing the date range to 90 days or less"
        
        # Multiple systems with large date range
        if system_count > 5 and days > 30:
            return True, "Consider reducing the number of systems or date range"
        
        return False, None
