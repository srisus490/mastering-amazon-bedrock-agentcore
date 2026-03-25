"""Cache manager for AI insights responses."""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.ai.config import ai_config
from src.ai.logger import ai_logger, log_cache_operation
from src.database.connection import get_db_session
from src.database.models import DashboardCacheModel


class CacheManager:
    """
    Manages caching of AI insights in SQLite database.
    
    Provides cache key generation, retrieval, storage, and cleanup
    with configurable TTL values for different insight types.
    """
    
    def __init__(self):
        """Initialize cache manager."""
        ai_logger.info("CacheManager initialized")
    
    def generate_cache_key(
        self,
        insight_type: str,
        source_system_id: str,
        **params: Any
    ) -> str:
        """
        Generate unique cache key from parameters.
        
        Uses SHA-256 hash of sorted parameters to ensure uniqueness
        and prevent cache collisions.
        
        Args:
            insight_type: Type of insight (insights, forecast, root_cause)
            source_system_id: Source system identifier
            **params: Additional parameters (dates, days, etc.)
            
        Returns:
            Unique cache key string
        """
        # Create a deterministic string from parameters
        # Sort keys to ensure consistent ordering
        param_dict = {
            "insight_type": insight_type,
            "source_system_id": source_system_id,
            **params
        }
        
        # Sort and serialize
        sorted_params = json.dumps(param_dict, sort_keys=True)
        
        # Generate hash
        cache_key = hashlib.sha256(sorted_params.encode()).hexdigest()
        
        log_cache_operation(
            "generate_key",
            cache_key,
            insight_type=insight_type,
            source_system_id=source_system_id
        )
        
        return f"ai_{insight_type}_{cache_key[:16]}"
    
    def get_cached_insight(
        self,
        cache_key: str,
        ignore_ttl: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached insight if valid.
        
        Args:
            cache_key: Cache key to retrieve
            ignore_ttl: If True, return cached data even if expired
            
        Returns:
            Cached data dictionary or None if not found/expired
        """
        try:
            with get_db_session() as session:
                cache_entry = session.query(DashboardCacheModel).filter(
                    DashboardCacheModel.cache_key == cache_key
                ).first()
                
                if not cache_entry:
                    log_cache_operation("miss", cache_key, reason="not_found")
                    return None
                
                # Check if expired (unless ignore_ttl is True)
                if not ignore_ttl:
                    now = datetime.utcnow()
                    if cache_entry.expires_at < now:
                        log_cache_operation(
                            "miss",
                            cache_key,
                            reason="expired",
                            expired_at=cache_entry.expires_at.isoformat()
                        )
                        return None
                
                # Parse cached JSON data
                try:
                    cached_data = json.loads(cache_entry.cache_value)
                    cached_data["cached"] = True
                    
                    if ignore_ttl and cache_entry.expires_at < datetime.utcnow():
                        cached_data["stale"] = True
                    
                    log_cache_operation(
                        "hit",
                        cache_key,
                        age_seconds=(datetime.utcnow() - cache_entry.created_at).total_seconds()
                    )
                    
                    return cached_data
                    
                except json.JSONDecodeError as e:
                    ai_logger.error(
                        "Failed to parse cached data",
                        cache_key=cache_key,
                        error=str(e)
                    )
                    return None
                    
        except Exception as e:
            ai_logger.error(
                "Error retrieving cached insight",
                cache_key=cache_key,
                error=str(e)
            )
            return None
    
    def set_cached_insight(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl_seconds: int
    ) -> None:
        """
        Store insight in cache with TTL.
        
        Args:
            cache_key: Cache key to store under
            data: Data dictionary to cache
            ttl_seconds: Time-to-live in seconds
        """
        try:
            with get_db_session() as session:
                # Calculate expiration time
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                
                # Serialize data
                cache_value = json.dumps(data)
                
                # Check if entry exists
                existing = session.query(DashboardCacheModel).filter(
                    DashboardCacheModel.cache_key == cache_key
                ).first()
                
                if existing:
                    # Update existing entry
                    existing.cache_value = cache_value
                    existing.expires_at = expires_at
                    existing.created_at = datetime.utcnow()
                else:
                    # Create new entry
                    cache_entry = DashboardCacheModel(
                        cache_key=cache_key,
                        cache_value=cache_value,
                        expires_at=expires_at
                    )
                    session.add(cache_entry)
                
                session.commit()
                
                log_cache_operation(
                    "set",
                    cache_key,
                    ttl_seconds=ttl_seconds,
                    expires_at=expires_at.isoformat()
                )
                
        except Exception as e:
            ai_logger.error(
                "Error storing cached insight",
                cache_key=cache_key,
                error=str(e)
            )
            # Don't raise - caching failures shouldn't break the application
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        try:
            with get_db_session() as session:
                now = datetime.utcnow()
                
                deleted_count = session.query(DashboardCacheModel).filter(
                    DashboardCacheModel.expires_at < now,
                    DashboardCacheModel.cache_key.like("ai_%")  # Only AI cache entries
                ).delete()
                
                session.commit()
                
                if deleted_count > 0:
                    ai_logger.info(
                        "Cleaned up expired AI cache entries",
                        count=deleted_count
                    )
                
                return deleted_count
                
        except Exception as e:
            ai_logger.error(
                "Error cleaning up expired cache",
                error=str(e)
            )
            return 0
    
    def get_ttl_for_insight_type(self, insight_type: str) -> int:
        """
        Get TTL in seconds for a specific insight type.
        
        Args:
            insight_type: Type of insight (insights, forecast, root_cause)
            
        Returns:
            TTL in seconds
        """
        ttl_map = {
            "insights": ai_config.ai_cache_ttl_insights,
            "forecast": ai_config.ai_cache_ttl_forecast,
            "root_cause": ai_config.ai_cache_ttl_root_cause,
        }
        
        return ttl_map.get(insight_type, ai_config.ai_cache_ttl_insights)
    
    def invalidate_cache(self, source_system_id: str) -> int:
        """
        Invalidate all cache entries for a specific system.
        
        Useful when system data changes significantly.
        
        Args:
            source_system_id: Source system identifier
            
        Returns:
            Number of entries invalidated
        """
        try:
            with get_db_session() as session:
                # Find all cache entries for this system
                # Cache keys contain system ID in the hash, so we need to check the value
                entries = session.query(DashboardCacheModel).filter(
                    DashboardCacheModel.cache_key.like("ai_%")
                ).all()
                
                deleted_count = 0
                for entry in entries:
                    try:
                        data = json.loads(entry.cache_value)
                        if data.get("source_system_id") == source_system_id:
                            session.delete(entry)
                            deleted_count += 1
                    except json.JSONDecodeError:
                        continue
                
                session.commit()
                
                if deleted_count > 0:
                    ai_logger.info(
                        "Invalidated cache for system",
                        source_system_id=source_system_id,
                        count=deleted_count
                    )
                
                return deleted_count
                
        except Exception as e:
            ai_logger.error(
                "Error invalidating cache",
                source_system_id=source_system_id,
                error=str(e)
            )
            return 0
