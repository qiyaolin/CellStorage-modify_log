"""
Lineage Cache Service - App Engine compatible caching for batch lineage data
"""
import json
import time
from datetime import datetime, timedelta
from flask import current_app
from .. import db


class LineageCacheService:
    """
    App Engine compatible caching service for lineage data
    Uses in-memory caching for App Engine deployment
    """
    
    # In-memory cache for App Engine (instance-level)
    _cache = {}
    _cache_timestamps = {}
    _max_cache_size = 100  # Limit cache size for memory efficiency
    _default_ttl = 300  # 5 minutes default TTL
    
    @classmethod
    def _generate_cache_key(cls, prefix, batch_id, **kwargs):
        """Generate a consistent cache key"""
        key_parts = [prefix, str(batch_id)]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    @classmethod
    def _is_cache_valid(cls, cache_key, ttl):
        """Check if cached data is still valid"""
        if cache_key not in cls._cache_timestamps:
            return False
        
        cache_time = cls._cache_timestamps[cache_key]
        return (time.time() - cache_time) < ttl
    
    @classmethod
    def _cleanup_old_cache(cls):
        """Remove old cache entries to manage memory"""
        current_time = time.time()
        keys_to_remove = []
        
        # Remove expired entries
        for key, timestamp in cls._cache_timestamps.items():
            if (current_time - timestamp) > cls._default_ttl * 2:  # Keep for double TTL
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            cls._cache.pop(key, None)
            cls._cache_timestamps.pop(key, None)
        
        # If cache is still too large, remove oldest entries
        if len(cls._cache) > cls._max_cache_size:
            # Sort by timestamp and remove oldest
            sorted_items = sorted(cls._cache_timestamps.items(), key=lambda x: x[1])
            items_to_remove = len(cls._cache) - cls._max_cache_size + 10  # Remove extra for buffer
            
            for i in range(items_to_remove):
                if i < len(sorted_items):
                    key = sorted_items[i][0]
                    cls._cache.pop(key, None)
                    cls._cache_timestamps.pop(key, None)
    
    @classmethod
    def get_cached_data(cls, cache_key, ttl=None):
        """Get data from cache if valid"""
        if ttl is None:
            ttl = cls._default_ttl
        
        try:
            if cls._is_cache_valid(cache_key, ttl):
                return cls._cache.get(cache_key)
        except Exception as e:
            current_app.logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    @classmethod
    def set_cached_data(cls, cache_key, data, ttl=None):
        """Set data in cache"""
        if ttl is None:
            ttl = cls._default_ttl
        
        try:
            # Cleanup old cache periodically
            if len(cls._cache) > cls._max_cache_size * 0.8:
                cls._cleanup_old_cache()
            
            cls._cache[cache_key] = data
            cls._cache_timestamps[cache_key] = time.time()
            
        except Exception as e:
            current_app.logger.warning(f"Cache storage error: {e}")
    
    @classmethod
    def invalidate_batch_cache(cls, batch_id):
        """Invalidate all cache entries for a specific batch"""
        try:
            keys_to_remove = []
            batch_str = str(batch_id)
            
            for key in cls._cache.keys():
                if batch_str in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                cls._cache.pop(key, None)
                cls._cache_timestamps.pop(key, None)
                
        except Exception as e:
            current_app.logger.warning(f"Cache invalidation error: {e}")
    
    @classmethod
    def get_cached_lineage(cls, batch_id, viewport_depth=3, include_details=True):
        """Get cached optimized lineage data"""
        cache_key = cls._generate_cache_key(
            "lineage_optimized", 
            batch_id, 
            depth=viewport_depth, 
            details=include_details
        )
        
        return cls.get_cached_data(cache_key)
    
    @classmethod
    def set_cached_lineage(cls, batch_id, data, viewport_depth=3, include_details=True):
        """Cache optimized lineage data"""
        cache_key = cls._generate_cache_key(
            "lineage_optimized", 
            batch_id, 
            depth=viewport_depth, 
            details=include_details
        )
        
        cls.set_cached_data(cache_key, data)
    
    @classmethod
    def get_cached_summary_stats(cls, batch_id):
        """Get cached summary statistics"""
        cache_key = cls._generate_cache_key("lineage_summary", batch_id)
        return cls.get_cached_data(cache_key, ttl=600)  # 10 minutes for stats
    
    @classmethod
    def set_cached_summary_stats(cls, batch_id, stats_data):
        """Cache summary statistics"""
        cache_key = cls._generate_cache_key("lineage_summary", batch_id)
        cls.set_cached_data(cache_key, stats_data, ttl=600)  # 10 minutes for stats
    
    @classmethod
    def get_cached_depth_nodes(cls, batch_id, depth_level, node_type, offset=0, limit=50):
        """Get cached depth nodes"""
        cache_key = cls._generate_cache_key(
            "lineage_depth",
            batch_id,
            depth=depth_level,
            type=node_type,
            offset=offset,
            limit=limit
        )
        
        return cls.get_cached_data(cache_key)
    
    @classmethod
    def set_cached_depth_nodes(cls, batch_id, data, depth_level, node_type, offset=0, limit=50):
        """Cache depth nodes data"""
        cache_key = cls._generate_cache_key(
            "lineage_depth",
            batch_id,
            depth=depth_level,
            type=node_type,
            offset=offset,
            limit=limit
        )
        
        cls.set_cached_data(cache_key, data)
    
    @classmethod
    def get_cache_stats(cls):
        """Get cache usage statistics for monitoring"""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for key, timestamp in cls._cache_timestamps.items():
            if (current_time - timestamp) < cls._default_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(cls._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'max_cache_size': cls._max_cache_size,
            'cache_usage_percent': (len(cls._cache) / cls._max_cache_size) * 100,
            'default_ttl': cls._default_ttl,
            'last_cleanup': datetime.now().isoformat()
        }
    
    @classmethod
    def clear_all_cache(cls):
        """Clear all cache data (for debugging/maintenance)"""
        cls._cache.clear()
        cls._cache_timestamps.clear()
        current_app.logger.info("All lineage cache cleared")
    
    @classmethod
    def warm_cache_for_batch(cls, batch_id):
        """Pre-warm cache for a batch with common queries"""
        try:
            from .batch_lineage_service import BatchLineageService
            
            # Pre-load commonly used data
            summary_stats = BatchLineageService.get_lineage_summary_stats(batch_id)
            cls.set_cached_summary_stats(batch_id, summary_stats)
            
            # Pre-load optimized lineage for default viewport
            optimized_lineage = BatchLineageService.get_optimized_lineage_for_frontend(batch_id)
            cls.set_cached_lineage(batch_id, optimized_lineage)
            
            current_app.logger.info(f"Cache warmed for batch {batch_id}")
            
        except Exception as e:
            current_app.logger.warning(f"Cache warming failed for batch {batch_id}: {e}")