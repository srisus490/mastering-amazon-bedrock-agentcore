"""Bedrock Agent for intelligent file monitoring queries"""

import json
from typing import Dict, Optional

import boto3

from src.core.logging import get_logger

logger = get_logger(__name__)


class FileMonitoringAgent:
    """
    Bedrock Agent that can query and analyze file monitoring data using natural language.
    
    Examples of queries:
    - "Show me systems with SLA violations today"
    - "Which system has the most files this week?"
    - "Predict file arrivals for PROD_SALES tomorrow"
    - "Analyze anomalies in the inventory system"
    - "What's the average SLA score across all systems?"
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_alias_id: str,
        region: str = "us-east-1",
    ):
        """
        Initialize Bedrock Agent.
        
        Args:
            agent_id: Bedrock Agent ID
            agent_alias_id: Agent alias ID
            region: AWS region
        """
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=region)
        
        logger.info(
            "FileMonitoringAgent initialized",
            agent_id=agent_id,
            agent_alias_id=agent_alias_id,
        )
    
    def query(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        enable_trace: bool = False,
    ) -> Dict:
        """
        Query the Bedrock Agent with natural language.
        
        Args:
            user_input: Natural language query
            session_id: Session ID for conversation continuity
            enable_trace: Enable trace for debugging
            
        Returns:
            Dictionary with agent response and metadata
        """
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        logger.info(
            "Querying Bedrock Agent",
            user_input=user_input[:100],
            session_id=session_id,
        )
        
        try:
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=user_input,
                enableTrace=enable_trace,
            )
            
            # Process streaming response
            result_text = ""
            traces = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result_text += chunk['bytes'].decode('utf-8')
                
                if enable_trace and 'trace' in event:
                    traces.append(event['trace'])
            
            logger.info(
                "Agent query completed",
                session_id=session_id,
                response_length=len(result_text),
            )
            
            return {
                "response": result_text,
                "session_id": session_id,
                "traces": traces if enable_trace else None,
            }
            
        except Exception as e:
            logger.error(
                "Agent query failed",
                user_input=user_input[:100],
                error=str(e),
            )
            raise
    
    def query_with_context(
        self,
        user_input: str,
        context: Dict,
        session_id: Optional[str] = None,
    ) -> Dict:
        """
        Query agent with additional context.
        
        Args:
            user_input: Natural language query
            context: Additional context (e.g., current system, date range)
            session_id: Session ID
            
        Returns:
            Dictionary with response
        """
        # Enhance query with context
        enhanced_input = f"""Context: {json.dumps(context)}

User Query: {user_input}"""
        
        return self.query(enhanced_input, session_id)
    
    def start_conversation(self) -> str:
        """
        Start a new conversation session.
        
        Returns:
            New session ID
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        logger.info("Started new conversation", session_id=session_id)
        return session_id
    
    def end_conversation(self, session_id: str) -> None:
        """
        End a conversation session.
        
        Args:
            session_id: Session to end
        """
        # Bedrock Agent sessions expire automatically
        logger.info("Ended conversation", session_id=session_id)


class AgentOrchestrator:
    """
    Orchestrates multiple AI capabilities for complex queries.
    
    Combines:
    - Bedrock Agent for natural language understanding
    - Anomaly Detector for pattern analysis
    - Direct database queries for real-time data
    """
    
    def __init__(
        self,
        agent: FileMonitoringAgent,
        anomaly_detector: 'BedrockAnomalyDetector',
    ):
        """
        Initialize orchestrator.
        
        Args:
            agent: Bedrock Agent instance
            anomaly_detector: Anomaly detector instance
        """
        self.agent = agent
        self.anomaly_detector = anomaly_detector
        logger.info("AgentOrchestrator initialized")
    
    def process_complex_query(
        self,
        user_input: str,
        session_id: Optional[str] = None,
    ) -> Dict:
        """
        Process complex queries that may require multiple AI calls.
        
        Args:
            user_input: User's natural language query
            session_id: Session ID
            
        Returns:
            Comprehensive response
        """
        logger.info("Processing complex query", user_input=user_input[:100])
        
        # Determine query type
        query_lower = user_input.lower()
        
        # Check if it's an anomaly detection request
        if any(word in query_lower for word in ['anomaly', 'anomalies', 'unusual', 'strange']):
            # Extract system ID if mentioned
            # This is simplified - in production, use NER or agent to extract entities
            system_id = self._extract_system_id(user_input)
            
            if system_id:
                anomaly_result = self.anomaly_detector.analyze_pattern(system_id)
                
                # Ask agent to summarize findings
                summary_query = f"""Based on this anomaly analysis, provide a user-friendly summary:
                
{json.dumps(anomaly_result, indent=2)}

Original question: {user_input}"""
                
                agent_response = self.agent.query(summary_query, session_id)
                
                return {
                    "type": "anomaly_analysis",
                    "detailed_analysis": anomaly_result,
                    "summary": agent_response["response"],
                    "session_id": agent_response["session_id"],
                }
        
        # Check if it's a prediction request
        elif any(word in query_lower for word in ['predict', 'forecast', 'next week', 'tomorrow']):
            system_id = self._extract_system_id(user_input)
            
            if system_id:
                prediction = self.anomaly_detector.predict_next_week(system_id)
                
                summary_query = f"""Based on this prediction, provide a user-friendly summary:
                
{json.dumps(prediction, indent=2)}

Original question: {user_input}"""
                
                agent_response = self.agent.query(summary_query, session_id)
                
                return {
                    "type": "prediction",
                    "detailed_prediction": prediction,
                    "summary": agent_response["response"],
                    "session_id": agent_response["session_id"],
                }
        
        # Default: use agent directly
        return {
            "type": "general_query",
            **self.agent.query(user_input, session_id)
        }
    
    def _extract_system_id(self, text: str) -> Optional[str]:
        """
        Extract system ID from text.
        
        This is a simple implementation. In production, use:
        - Named Entity Recognition (NER)
        - Bedrock Agent's entity extraction
        - Database lookup of system names
        
        Args:
            text: Input text
            
        Returns:
            System ID if found
        """
        # Simple pattern matching
        from src.database.connection import get_db_session
        from src.database.models import SourceSystemModel
        
        try:
            with get_db_session() as session:
                systems = session.query(SourceSystemModel).all()
                
                for sys in systems:
                    _ = (sys.id, sys.name)
                    session.expunge(sys)
                    
                    # Check if system ID or name is in text
                    if sys.id.lower() in text.lower() or sys.name.lower() in text.lower():
                        return sys.id
        except:
            pass
        
        return None
