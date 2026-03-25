"""Query processor for natural language parsing and intent extraction."""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from src.core.logging import get_logger

logger = get_logger(__name__)


class QueryType(str, Enum):
    """Types of queries the system can handle."""
    SYSTEM_HEALTH = "SYSTEM_HEALTH"
    SLA_VIOLATIONS = "SLA_VIOLATIONS"
    FILE_TRENDS = "FILE_TRENDS"
    SYSTEM_COMPARISON = "SYSTEM_COMPARISON"
    ROOT_CAUSE = "ROOT_CAUSE"
    GENERAL_INFO = "GENERAL_INFO"
    AMBIGUOUS = "AMBIGUOUS"
    UNPARSEABLE = "UNPARSEABLE"


class QueryIntent:
    """Represents the parsed intent of a user query."""
    
    def __init__(
        self,
        query_type: QueryType,
        system_ids: List[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        filters: Dict = None,
        confidence: float = 1.0,
        ambiguity_reason: Optional[str] = None
    ):
        self.query_type = query_type
        self.system_ids = system_ids or []
        self.date_range = date_range
        self.filters = filters or {}
        self.confidence = confidence
        self.ambiguity_reason = ambiguity_reason


class QueryProcessor:
    """Processes natural language queries and extracts intent."""
    
    # Query type patterns
    HEALTH_PATTERNS = [
        r'\b(how|status|health|doing|performing)\b.*\b(system|is|are)\b',
        r'\b(check|show|get|tell me about)\b.*\b(status|health)\b',
        r'\b(is|are)\b.*\b(up|down|running|working|healthy|ok|okay)\b',
        r'\bhow\s+(is|are)\b'  # "how is X" or "how are X"
    ]
    
    VIOLATION_PATTERNS = [
        r'\b(violation|violations|breach|breaches|miss|missed)\b',
        r'\b(sla|service level)\b.*\b(violation|breach|miss)\b',
        r'\b(show|get|list|find)\b.*\b(violation|breach)\b'
    ]
    
    TREND_PATTERNS = [
        r'\b(trend|trends|pattern|patterns)\b',
        r'\b(over time|historical|history)\b',
        r'\b(daily|weekly|monthly)\b.*\b(pattern|trend)\b'
    ]
    
    COMPARISON_PATTERNS = [
        r'\b(compare|comparison|versus|vs|against)\b',
        r'\b(difference|differences)\b.*\b(between|among)\b'
    ]
    
    ROOT_CAUSE_PATTERNS = [
        r'\b(why|reason|cause|root cause)\b',
        r'\b(what caused|what\'s causing)\b',
        r'\b(explain|analyze)\b.*\b(problem|issue|failure)\b'
    ]
    
    # Date reference patterns
    DATE_PATTERNS = {
        'today': lambda: (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                         datetime.now()),
        'yesterday': lambda: (
            (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59)
        ),
        'last week': lambda: (
            datetime.now() - timedelta(days=7),
            datetime.now()
        ),
        'last month': lambda: (
            datetime.now() - timedelta(days=30),
            datetime.now()
        ),
        'last 7 days': lambda: (
            datetime.now() - timedelta(days=7),
            datetime.now()
        ),
        'last 30 days': lambda: (
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
    }
    
    # Context reference patterns
    CONTEXT_REFERENCES = [
        r'\b(it|that|this|the same|same)\b',
        r'\b(that system|this system|the system)\b'
    ]
    
    def __init__(self, available_systems: Optional[List[str]] = None):
        """
        Initialize the query processor.
        
        Args:
            available_systems: List of available system IDs for validation
        """
        self.available_systems = available_systems or []
    
    def parseQuery(
        self,
        query: str,
        context: Optional[List[Dict]] = None
    ) -> QueryIntent:
        """
        Parse a natural language query and extract intent.
        
        Args:
            query: User's natural language query
            context: Previous messages for context resolution
            
        Returns:
            QueryIntent object with parsed information
        """
        query_lower = query.lower().strip()
        
        # Identify query type
        query_type = self.identifyQueryType(query_lower)
        
        # Extract system names
        system_ids = self.extractSystemNames(query)
        
        # Resolve context references if no systems found
        if not system_ids and context:
            system_ids = self.resolveContextReferences(query_lower, context)
        
        # Extract date references
        date_range = self.extractDateReferences(query_lower)
        
        # Determine confidence and ambiguity
        confidence = 1.0
        ambiguity_reason = None
        
        if query_type == QueryType.AMBIGUOUS:
            confidence = 0.5
            ambiguity_reason = "Multiple interpretations possible"
        elif query_type == QueryType.UNPARSEABLE:
            confidence = 0.0
            ambiguity_reason = "Could not understand query"
        
        return QueryIntent(
            query_type=query_type,
            system_ids=system_ids,
            date_range=date_range,
            confidence=confidence,
            ambiguity_reason=ambiguity_reason
        )
    
    def identifyQueryType(self, query: str) -> QueryType:
        """
        Classify the query into a specific type.
        
        Args:
            query: Lowercase query string
            
        Returns:
            QueryType enum value
        """
        # Count matches for each type
        matches = {
            QueryType.SYSTEM_HEALTH: self._count_pattern_matches(query, self.HEALTH_PATTERNS),
            QueryType.SLA_VIOLATIONS: self._count_pattern_matches(query, self.VIOLATION_PATTERNS),
            QueryType.FILE_TRENDS: self._count_pattern_matches(query, self.TREND_PATTERNS),
            QueryType.SYSTEM_COMPARISON: self._count_pattern_matches(query, self.COMPARISON_PATTERNS),
            QueryType.ROOT_CAUSE: self._count_pattern_matches(query, self.ROOT_CAUSE_PATTERNS)
        }
        
        # Find the type with most matches
        max_matches = max(matches.values())
        
        if max_matches == 0:
            # No patterns matched
            if len(query.split()) < 3:
                return QueryType.UNPARSEABLE
            return QueryType.GENERAL_INFO
        
        # Check for ambiguity (multiple types with same high match count)
        top_types = [t for t, count in matches.items() if count == max_matches]
        if len(top_types) > 1:
            return QueryType.AMBIGUOUS
        
        return top_types[0]
    
    def extractSystemNames(self, query: str) -> List[str]:
        """
        Extract system names/IDs from the query.
        
        Args:
            query: User's query string
            
        Returns:
            List of system IDs found in the query
        """
        found_systems = []
        
        # Look for system IDs in the query
        for system_id in self.available_systems:
            # Check for exact match (case-insensitive)
            if system_id.lower() in query.lower():
                found_systems.append(system_id)
                continue
            
            # Check for system name variations (e.g., "PROD_SALES" -> "prod sales", "sales")
            system_parts = system_id.lower().replace('_', ' ').replace('-', ' ').split()
            for part in system_parts:
                if len(part) > 3 and part in query.lower():
                    if system_id not in found_systems:
                        found_systems.append(system_id)
                        break
        
        return found_systems
    
    def extractDateReferences(self, query: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Parse date mentions in the query.
        
        Args:
            query: Lowercase query string
            
        Returns:
            Tuple of (start_date, end_date) or None
        """
        for pattern, date_func in self.DATE_PATTERNS.items():
            if pattern in query:
                return date_func()
        
        # Check for specific date patterns like "from X to Y"
        # This is a simplified implementation
        return None
    
    def resolveContextReferences(
        self,
        query: str,
        context: List[Dict]
    ) -> List[str]:
        """
        Resolve references like "it", "that system" using conversation context.
        
        Args:
            query: Lowercase query string
            context: Previous messages
            
        Returns:
            List of system IDs from context
        """
        # Check if query contains context references
        has_reference = any(
            re.search(pattern, query)
            for pattern in self.CONTEXT_REFERENCES
        )
        
        if not has_reference:
            return []
        
        # Look through recent context for system mentions
        # Search in reverse order (most recent first)
        for message in reversed(context[-5:]):  # Check last 5 messages
            if message.get('role') == 'assistant':
                # Check if assistant mentioned any systems
                content = message.get('content', '').lower()
                for system_id in self.available_systems:
                    if system_id.lower() in content:
                        return [system_id]
            
            elif message.get('role') == 'user':
                # Check previous user queries
                content = message.get('content', '')
                systems = self.extractSystemNames(content)
                if systems:
                    return systems
        
        return []
    
    def _count_pattern_matches(self, query: str, patterns: List[str]) -> int:
        """Count how many patterns match in the query."""
        count = 0
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                count += 1
        return count
    
    def getSuggestions(self, query_type: QueryType) -> List[str]:
        """
        Get suggestions for rephrasing based on query type.
        
        Args:
            query_type: The identified query type
            
        Returns:
            List of suggestion strings
        """
        if query_type == QueryType.UNPARSEABLE:
            return [
                "Try asking about system health: 'How is PROD_SALES doing?'",
                "Ask about violations: 'Show me violations from last week'",
                "Check trends: 'What's the trend for PROD_ANALYTICS?'",
                "Compare systems: 'Compare PROD_SALES and PROD_INVENTORY'"
            ]
        
        if query_type == QueryType.AMBIGUOUS:
            return [
                "Could you be more specific about what you'd like to know?",
                "Are you asking about system health, violations, or trends?"
            ]
        
        return []
