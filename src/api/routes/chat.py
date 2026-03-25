"""Chat API endpoints for conversational AI assistant."""

import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from src.ai.agent_action_handler import get_action_handler
from src.ai.chat_cache_manager import get_chat_cache
from src.ai.cost_monitor import get_cost_monitor
from src.ai.intelligent_query_parser import IntelligentQueryParser
from src.ai.knowledge_base_client import get_kb_client
from src.ai.models import ChatRequest, ChatResponse, TokenUsage
from src.ai.query_processor import QueryProcessor, QueryType
from src.ai.response_generator import ResponseGenerator
from src.ai.sql_query_generator import SQLQueryGenerator
from src.ai.cohere_client import (
    CohereAuthError,
    CohereRateLimitError,
    CohereTimeoutError,
    CohereUnavailableError,
    CohereError,
)
from src.core.logging import get_logger
from src.database.connection import get_db_session
from src.database.models import SourceSystemModel

logger = get_logger(__name__)

router = APIRouter()

# Initialize components
_query_processor = None
_intelligent_parser = None
_sql_generator = None
_response_generator = None
_cache_manager = None


def _get_intelligent_parser() -> IntelligentQueryParser:
    """Get or create intelligent query parser instance."""
    global _intelligent_parser
    if _intelligent_parser is None:
        # Get available systems from database
        with get_db_session() as session:
            systems = session.query(SourceSystemModel.id).all()
            system_ids = [s.id for s in systems]
        _intelligent_parser = IntelligentQueryParser(available_systems=system_ids)
    return _intelligent_parser


def _get_query_processor() -> QueryProcessor:
    """Get or create query processor instance."""
    global _query_processor
    if _query_processor is None:
        # Get available systems from database
        with get_db_session() as session:
            systems = session.query(SourceSystemModel.id).all()
            system_ids = [s.id for s in systems]
        _query_processor = QueryProcessor(available_systems=system_ids)
    return _query_processor


def _get_sql_generator() -> SQLQueryGenerator:
    """Get or create SQL generator instance."""
    global _sql_generator
    if _sql_generator is None:
        _sql_generator = SQLQueryGenerator()
    return _sql_generator


def _get_response_generator() -> ResponseGenerator:
    """Get or create response generator instance."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator


def _get_cache_manager():
    """Get cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = get_chat_cache()
    return _cache_manager


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest) -> ChatResponse:
    """
    Process a natural language query and return an AI-generated response.
    
    This endpoint:
    1. Checks cache for recent identical queries
    2. Parses the natural language query
    3. Generates and executes SQL queries
    4. Uses Bedrock to generate natural language responses
    5. Caches the response for future use
    """
    try:
        # Get components
        intelligent_parser = _get_intelligent_parser()
        sql_generator = _get_sql_generator()
        response_generator = _get_response_generator()
        cache_manager = _get_cache_manager()
        cost_monitor = get_cost_monitor()
        
        # Check circuit breaker
        if cost_monitor.isCircuitBreakerActive():
            logger.warning("Circuit breaker active - rejecting query")
            raise HTTPException(
                status_code=503,
                detail="Chat service temporarily disabled due to cost limits. Please try again later."
            )
        
        # Check cache first
        query_hash = cache_manager.generateQueryHash(request.query, request.context)
        cached_response = cache_manager.getCachedResponse(query_hash)
        
        if cached_response:
            logger.info("Returning cached response")
            return ChatResponse(**cached_response, cached=True)
        
        # Parse the query using intelligent parser
        context_dicts = [msg.dict() for msg in request.context] if request.context else []
        parsed = intelligent_parser.parseQuery(request.query, context_dicts)
        
        logger.info(
            f"Parsed query intent",
            query_type=parsed['intent'],
            system_ids=parsed['systems'],
            confidence=parsed['confidence'],
            is_greeting=parsed['is_greeting']
        )
        
        # Handle greetings
        if parsed['is_greeting']:
            greeting = parsed.get('greeting_response') or "Hello! How can I help you with the file monitoring dashboard today?"
            return ChatResponse(
                response=greeting,
                data=None,
                suggestions=[
                    "Show me system health",
                    "What violations occurred recently?",
                    "How is PROD_BACKUP doing?"
                ],
                cached=False,
                tokens_used=TokenUsage(input=50, output=20, cached=0)
            )
        
        # Handle out-of-scope queries — let Cohere answer general questions
        if parsed.get('is_out_of_scope'):
            from src.ai.cohere_client import CohereClient
            cohere = CohereClient()
            general_answer = cohere.invoke_model(prompt=request.query, max_tokens=300)
            return ChatResponse(
                response=general_answer,
                data=None,
                suggestions=[
                    "Show me system health",
                    "What violations occurred recently?",
                    "Compare PROD_SALES and PROD_INVENTORY"
                ],
                cached=False,
                tokens_used=TokenUsage(input=50, output=len(general_answer.split()), cached=0)
            )
        
        # Handle low confidence
        if parsed['confidence'] < 0.5:
            return ChatResponse(
                response="I'm not sure I understand. Could you rephrase your question?",
                data=None,
                suggestions=[
                    "How is PROD_SALES doing?",
                    "Show me violations from last week",
                    "Compare PROD_SALES and PROD_INVENTORY"
                ],
                cached=False,
                tokens_used=TokenUsage(input=0, output=0, cached=0)
            )
        
        intent = parsed['intent']
        system_ids = parsed['systems']
        date_range = parsed['date_range']
        
        # Check if query would be expensive
        is_expensive, suggestion = sql_generator.isExpensiveQuery(
            date_range,
            len(system_ids)
        )
        if is_expensive:
            return ChatResponse(
                response=f"This query might take a while. {suggestion}",
                data=None,
                suggestions=["Try a shorter date range", "Focus on one system"],
                cached=False,
                tokens_used=TokenUsage(input=0, output=0, cached=0)
            )
        
        # Generate and execute SQL query
        query_result = None
        
        if intent == "SYSTEM_HEALTH":
            if not system_ids:
                return ChatResponse(
                    response="Which system would you like to check?",
                    data=None,
                    suggestions=["PROD_SALES", "PROD_ANALYTICS", "PROD_INVENTORY"],
                    cached=False,
                    tokens_used=TokenUsage(input=0, output=0, cached=0)
                )
            
            sql, params = sql_generator.generateHealthQuery(
                system_ids[0],
                date_range
            )
            query_result = _execute_query(sql, params)
        
        elif intent == "SLA_VIOLATIONS":
            filters = {
                'system_ids': system_ids,
                'date_range': date_range
            }
            sql, params = sql_generator.generateViolationsQuery(filters)
            query_result = _execute_query(sql, params)
        
        elif intent == "FILE_TRENDS":
            if not system_ids:
                return ChatResponse(
                    response="Which system's trends would you like to see?",
                    data=None,
                    suggestions=["Show trends for PROD_SALES"],
                    cached=False,
                    tokens_used=TokenUsage(input=0, output=0, cached=0)
                )
            
            sql, params = sql_generator.generateTrendsQuery(
                system_ids[0],
                date_range or _get_default_date_range()
            )
            query_result = _execute_query(sql, params)
        
        elif intent == "SYSTEM_COMPARISON":
            if len(system_ids) < 2:
                return ChatResponse(
                    response="Please specify at least two systems to compare.",
                    data=None,
                    suggestions=["Compare PROD_SALES and PROD_ANALYTICS"],
                    cached=False,
                    tokens_used=TokenUsage(input=0, output=0, cached=0)
                )
            
            sql, params = sql_generator.generateComparisonQuery(
                system_ids,
                date_range
            )
            query_result = _execute_query(sql, params)
        
        elif intent == "GENERAL_INFO":
            # For general info, just list available systems
            with get_db_session() as session:
                systems = session.query(SourceSystemModel).filter_by(is_active=True).all()
                query_result = [
                    {'id': s.id, 'name': s.name, 'is_active': s.is_active}
                    for s in systems
                ]
        
        # Retrieve relevant context from Knowledge Base
        kb_client = get_kb_client()
        kb_context = None
        
        if kb_client.is_available():
            try:
                logger.info("Retrieving Knowledge Base context")
                retrieved_docs = kb_client.retrieve(
                    query=request.query,
                    max_results=5,
                    similarity_threshold=0.7
                )
                
                if retrieved_docs:
                    kb_context = kb_client.format_context(retrieved_docs)
                    logger.info(f"Retrieved {len(retrieved_docs)} KB documents")
                else:
                    logger.info("No relevant KB documents found")
            except Exception as e:
                logger.warning(f"KB retrieval failed, continuing without KB context: {e}")
        
        # Generate natural language response using Bedrock with KB context
        response_data = response_generator.generateResponse(
            query_result,
            request.query,
            context_dicts,
            kb_context=kb_context
        )
        
        # Generate suggestions
        suggestions = response_generator.generateSuggestions(
            intent.query_type.value,
            intent.system_ids
        )
        
        # Build response
        chat_response = ChatResponse(
            response=response_data['response'],
            data=query_result if query_result else None,
            suggestions=suggestions,
            cached=False,
            tokens_used=TokenUsage(**response_data['tokens_used'])
        )
        
        # Record token usage for cost monitoring
        cost_info = cost_monitor.recordTokenUsage(
            input_tokens=response_data['tokens_used']['input'],
            output_tokens=response_data['tokens_used']['output'],
            cached_tokens=response_data['tokens_used']['cached']
        )
        
        # Log any cost alerts
        if cost_info['alerts']:
            for alert in cost_info['alerts']:
                logger.warning(f"Cost alert: {alert}")
        
        # Cache the response
        cache_manager.setCachedResponse(
            query_hash,
            chat_response.dict(exclude={'cached'}),
            ttl=300  # 5 minutes
        )
        
        return chat_response
    
    except CohereAuthError as e:
        logger.error(f"Cohere authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="AI service authentication failed. Please check your COHERE_API_KEY."
        )
    
    except CohereRateLimitError as e:
        logger.error(f"Cohere rate limit error: {e}")
        raise HTTPException(
            status_code=429,
            detail="AI service rate limit exceeded. Please try again in a moment."
        )
    
    except CohereTimeoutError as e:
        logger.error(f"Cohere timeout error: {e}")
        raise HTTPException(
            status_code=504,
            detail="AI service request timed out. Please try again."
        )
    
    except CohereUnavailableError as e:
        logger.error(f"Cohere unavailable error: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again later."
        )
    
    except CohereError as e:
        logger.error(f"Cohere error: {e}")
        raise HTTPException(
            status_code=500,
            detail="AI service error. Please try again."
        )
    
    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your query.")


def _execute_query(sql: str, params: dict) -> List[dict]:
    """Execute a SQL query and return results as list of dicts."""
    sql_generator = _get_sql_generator()
    
    # Validate query
    if not sql_generator.validateQuery(sql):
        raise ValueError("Invalid SQL query")
    
    with get_db_session() as session:
        result = session.execute(text(sql), params)
        rows = result.fetchall()
        
        # Convert to list of dicts
        if rows:
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
        return []


def _get_default_date_range():
    """Get default date range (last 7 days)."""
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    return (start_date, end_date)


@router.post("/clear")
async def clear_chat():
    """
    Clear conversation cache.
    
    Clears all cached responses to free memory and force fresh queries.
    """
    try:
        cache_manager = _get_cache_manager()
        cache_manager.clearCache()
        
        logger.info("Chat cache cleared")
        
        return {
            "status": "success",
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/examples")
async def get_examples(system_id: str = None):
    """
    Get example questions for the chat interface.
    
    Returns context-aware examples based on selected system if provided.
    
    Args:
        system_id: Optional system ID for context-aware examples
    """
    try:
        # Base examples
        base_examples = [
            "How is PROD_SALES doing?",
            "Show me violations from last week",
            "What's the trend for PROD_ANALYTICS?",
            "Compare PROD_SALES and PROD_INVENTORY",
            "Why is PROD_SALES slow?"
        ]
        
        # If system_id provided, generate system-specific examples
        if system_id:
            with get_db_session() as session:
                system = session.query(SourceSystemModel).filter_by(id=system_id).first()
                if system:
                    return {
                        "examples": [
                            f"How is {system_id} doing?",
                            f"Show me violations for {system_id}",
                            f"What's the trend for {system_id}?",
                            f"Why is {system_id} having issues?",
                            "Compare all systems"
                        ]
                    }
        
        return {"examples": base_examples}
    
    except Exception as e:
        logger.error(f"Error getting examples: {e}")
        # Return base examples on error
        return {
            "examples": [
                "How is my system doing?",
                "Show me recent violations",
                "What are the trends?",
                "Compare systems"
            ]
        }


@router.get("/health")
async def chat_health():
    """
    Check chat service health.
    
    Verifies connectivity to Bedrock and database.
    """
    health_status = {
        "status": "healthy",
        "cohere": "unknown",
        "database": "unknown",
        "cache": "unknown"
    }
    
    try:
        # Check database
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
            health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    try:
        # Check Cohere credentials
        response_generator = _get_response_generator()
        if response_generator.bedrock_client.validate_credentials():
            health_status["cohere"] = "healthy"
        else:
            health_status["cohere"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Cohere health check failed: {e}")
        health_status["cohere"] = "unhealthy"
        health_status["status"] = "degraded"
    
    try:
        # Check Knowledge Base
        kb_client = get_kb_client()
        if kb_client.is_available():
            health_status["knowledge_base"] = "healthy"
            health_status["kb_id"] = kb_client.knowledge_base_id
        else:
            health_status["knowledge_base"] = "disabled"
    except Exception as e:
        logger.error(f"Knowledge Base health check failed: {e}")
        health_status["knowledge_base"] = "unhealthy"
    
    try:
        # Check cache
        cache_manager = _get_cache_manager()
        stats = cache_manager.getCacheStats()
        health_status["cache"] = "healthy"
        health_status["cache_stats"] = stats
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status["cache"] = "unhealthy"
    
    return health_status


@router.post("/agent", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """
    Process query using Cohere with real system data context.
    """
    try:
        from src.ai.cohere_client import CohereClient, CohereError

        cost_monitor = get_cost_monitor()
        if cost_monitor.isCircuitBreakerActive():
            raise HTTPException(status_code=503, detail="Chat service temporarily disabled.")

        cohere_client = CohereClient()
        query = request.query.strip()

        # --- Fetch real system data using dashboard context (selected system + date range) ---
        system_context_data = ""
        try:
            def fmt_ts(ts_str):
                if not ts_str:
                    return "N/A"
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(str(ts_str).replace("Z", ""))
                    return dt.strftime("%b %d, %Y %I:%M %p")
                except Exception:
                    return str(ts_str)

            # Extract date range from dashboard context if provided
            dash_ctx = request.dashboard_context or {}
            selected_system = dash_ctx.get("selected_system")
            start_date = dash_ctx.get("start_date")   # YYYY-MM-DD string or None
            end_date   = dash_ctx.get("end_date")     # YYYY-MM-DD string or None

            # Build date filter clause
            if start_date and end_date:
                date_filter = f"DATE(fa.arrival_timestamp) BETWEEN '{start_date}' AND '{end_date}'"
                date_label = f"{start_date} to {end_date}"
            else:
                date_filter = "DATE(fa.arrival_timestamp) = DATE('now')"
                date_label = "today"

            with get_db_session() as session:
                rows = session.execute(text(f"""
                    SELECT 
                        fa.source_system_id,
                        COUNT(*) as period_files,
                        MAX(fa.arrival_timestamp) as last_arrival,
                        COUNT(CASE WHEN DATE(fa.arrival_timestamp) = DATE('now') THEN 1 END) as today_count
                    FROM file_arrivals fa
                    WHERE {date_filter}
                    GROUP BY fa.source_system_id
                    ORDER BY fa.source_system_id
                """)).fetchall()

                if rows:
                    lines = [f"System data ({date_label}):"]
                    for r in rows:
                        lines.append(
                            f"  - {r[0]}: {r[1]} files in period, {r[3]} files today, "
                            f"last arrival: {fmt_ts(r[2])}"
                        )
                    system_context_data = "\n".join(lines)

                # Detailed trend for the mentioned or selected system
                query_upper = query.upper()
                mentioned_system = selected_system
                if not mentioned_system:
                    for r in rows:
                        if r[0].upper() in query_upper:
                            mentioned_system = r[0]
                            break

                if mentioned_system:
                    trend_rows = session.execute(text("""
                        SELECT 
                            DATE(arrival_timestamp) as day,
                            COUNT(*) as file_count
                        FROM file_arrivals
                        WHERE source_system_id = :sys
                          AND arrival_timestamp >= DATE('now', '-14 days')
                        GROUP BY DATE(arrival_timestamp)
                        ORDER BY day
                    """), {"sys": mentioned_system}).fetchall()

                    if trend_rows:
                        trend_lines = [f"\nLast 14 days trend for {mentioned_system}:"]
                        for tr in trend_rows:
                            trend_lines.append(f"  {tr[0]}: {tr[1]} files")
                        system_context_data += "\n".join(trend_lines)

                    # Also pull SLA violations for the system in the active date range
                    viol_filter = f"violation_date BETWEEN '{start_date}' AND '{end_date}'" if start_date and end_date else "violation_date >= DATE('now', '-7 days')"
                    viol_rows = session.execute(text(f"""
                        SELECT severity, COUNT(*) as cnt
                        FROM sla_violations
                        WHERE source_system_id = :sys AND {viol_filter}
                        GROUP BY severity
                    """), {"sys": mentioned_system}).fetchall()

                    if viol_rows:
                        viol_lines = [f"\nSLA violations for {mentioned_system} ({date_label}):"]
                        for vr in viol_rows:
                            viol_lines.append(f"  {vr[0]}: {vr[1]}")
                        system_context_data += "\n".join(viol_lines)

        except Exception as db_err:
            logger.warning(f"Could not fetch system data for agent context: {db_err}")

        # Build a focused, concise prompt
        system_prompt = (
            "You are a concise AI assistant for a file monitoring dashboard. "
            "Answer questions about system health, file trends, and SLA using the data provided. "
            "For general questions (time, weather, coding, etc.) answer directly. "
            "Keep answers SHORT and to the point — 2-4 sentences max unless a list is needed. "
            "Do NOT output raw ISO timestamps like 2026-03-21T20:51:48. "
            "Always write dates in a human-friendly format like 'Mar 21, 2026 8:51 PM'. "
            "Do NOT ask clarifying questions if you have enough data to answer. "
            "Do NOT repeat the question back. Just answer."
        )

        context_block = f"\n\nDashboard Data:\n{system_context_data}" if system_context_data else ""
        full_prompt = f"{system_prompt}{context_block}\n\nUser: {query}\nAssistant:"

        logger.info(f"Invoking Cohere agent for: {query[:100]}")
        response_text = cohere_client.invoke_model(prompt=full_prompt, max_tokens=300)

        # Strip any "Assistant:" prefix Cohere might echo back
        response_text = response_text.strip()
        if response_text.lower().startswith("assistant:"):
            response_text = response_text[10:].strip()

        # Detect comparison queries — attach a report URL so the frontend can render a link
        comparison_keywords = ["compare", "comparison", "all systems", "vs", "versus", "rank", "ranking", "best", "worst"]
        is_comparison = any(kw in query.lower() for kw in comparison_keywords)
        report_url = None
        if is_comparison:
            params = []
            if start_date: params.append(f"start_date={start_date}")
            if end_date:   params.append(f"end_date={end_date}")
            qs = ("?" + "&".join(params)) if params else ""
            report_url = f"comparison.html{qs}"

        return ChatResponse(
            response=response_text,
            data={"report_url": report_url} if report_url else None,
            suggestions=["Show me all systems", "Any SLA violations?", "Compare systems"],
            cached=False,
            tokens_used=TokenUsage(
                input=int(len(full_prompt.split()) * 1.3),
                output=int(len(response_text.split()) * 1.3),
                cached=0,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error with Cohere agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    kb_client = get_kb_client()
    
    health_info = {
        'status': 'healthy',
        'agent_type': 'bedrock-agentcore-runtime',
        'kb_configured': kb_client.is_available(),
        'timestamp': datetime.now().isoformat()
    }
    
    # Check if runtime agent is configured
    try:
        agent_arn = os.environ.get("AGENTCORE_RUNTIME_AGENT_ARN")
        if agent_arn:
            health_info['agent_configured'] = True
            health_info['agent_arn'] = agent_arn
        else:
            health_info['agent_configured'] = False
            health_info['status'] = 'degraded'
    except Exception as e:
        logger.error(f"Error checking agent configuration: {e}")
        health_info['agent_configured'] = False
        health_info['status'] = 'degraded'
    
    return health_info


@router.get("/compare")
async def get_comparison_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """
    Return a full structured comparison of all systems for the comparison report page.
    """
    try:
        if start_date and end_date:
            date_filter = f"DATE(fa.arrival_timestamp) BETWEEN '{start_date}' AND '{end_date}'"
            viol_filter = f"violation_date BETWEEN '{start_date}' AND '{end_date}'"
            date_label = f"{start_date} to {end_date}"
        else:
            date_filter = "DATE(fa.arrival_timestamp) >= DATE('now', '-30 days')"
            viol_filter = "violation_date >= DATE('now', '-30 days')"
            date_label = "Last 30 days"

        with get_db_session() as session:
            # File counts per system
            file_rows = session.execute(text(f"""
                SELECT
                    fa.source_system_id,
                    COUNT(*) as file_count,
                    MAX(fa.arrival_timestamp) as last_arrival,
                    SUM(fa.file_size_bytes) as total_bytes
                FROM file_arrivals fa
                WHERE {date_filter}
                GROUP BY fa.source_system_id
                ORDER BY file_count DESC
            """)).fetchall()

            # SLA scores per system
            score_rows = session.execute(text(f"""
                SELECT source_system_id, AVG(CAST(score AS FLOAT)) as avg_score
                FROM sla_scores
                WHERE score_date BETWEEN COALESCE('{start_date}', DATE('now','-30 days'))
                                     AND COALESCE('{end_date}', DATE('now'))
                GROUP BY source_system_id
            """)).fetchall()
            scores = {r.source_system_id: round(float(r.avg_score), 1) for r in score_rows}

            # Violation counts per system
            viol_rows = session.execute(text(f"""
                SELECT source_system_id,
                       COUNT(*) as total,
                       SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) as critical,
                       SUM(CASE WHEN severity='high'     THEN 1 ELSE 0 END) as high,
                       SUM(CASE WHEN severity='medium'   THEN 1 ELSE 0 END) as medium,
                       SUM(CASE WHEN severity='low'      THEN 1 ELSE 0 END) as low
                FROM sla_violations
                WHERE {viol_filter}
                GROUP BY source_system_id
            """)).fetchall()
            viols = {r.source_system_id: {
                "total": r.total, "critical": r.critical,
                "high": r.high, "medium": r.medium, "low": r.low
            } for r in viol_rows}

        def fmt_bytes(b):
            if b is None: return "N/A"
            b = int(b)
            if b >= 1_073_741_824: return f"{b/1_073_741_824:.1f} GB"
            if b >= 1_048_576:     return f"{b/1_048_576:.1f} MB"
            if b >= 1_024:         return f"{b/1_024:.1f} KB"
            return f"{b} B"

        def fmt_ts(ts):
            if not ts: return "N/A"
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(str(ts).replace("Z",""))
                return dt.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                return str(ts)

        systems = []
        for r in file_rows:
            sid = r.source_system_id
            v = viols.get(sid, {"total":0,"critical":0,"high":0,"medium":0,"low":0})
            sla = scores.get(sid)
            # Derive worst severity
            worst = None
            for sev in ["critical","high","medium","low"]:
                if v.get(sev, 0) > 0:
                    worst = sev
                    break
            systems.append({
                "system_id": sid,
                "file_count": r.file_count,
                "total_size": fmt_bytes(r.total_bytes),
                "last_arrival": fmt_ts(r.last_arrival),
                "sla_score": sla,
                "violations": v,
                "worst_severity": worst,
            })

        return {
            "date_label": date_label,
            "start_date": start_date,
            "end_date": end_date,
            "systems": systems,
            "generated_at": datetime.now().strftime("%b %d, %Y %I:%M %p"),
        }

    except Exception as e:
        logger.error(f"Error generating comparison report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
