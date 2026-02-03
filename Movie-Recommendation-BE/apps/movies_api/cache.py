"""
Cache utilities for the Movie Nexus application
"""
from functools import wraps
from django.core.cache import cache
import hashlib
import json


def cache_key_generator(*args, **kwargs):
    """
    Generate a unique cache key from function arguments
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached_query(timeout=60*15, key_prefix='query'):
    """
    Decorator to cache database query results
    
    Usage:
        @cached_query(timeout=60*30, key_prefix='recommendations')
        def get_recommendations(user_id, limit=10):
            # Expensive database operations
            return results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Get fresh result
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


class CacheManager:
    """
    Utility class for managing cache operations
    """
    
    @staticmethod
    def invalidate_pattern(pattern):
        """
        Invalidate all cache keys matching a pattern
        
        Usage:
            CacheManager.invalidate_pattern('movie:*')
        """
        try:
            # Note: This requires Redis backend
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            # django-redis prepends the KEY_PREFIX from settings.
            # We need to include it when using raw redis-py commands
            prefix = "nexus_movie:"
            keys = redis_conn.keys(f"{prefix}{pattern}")
            if keys:
                redis_conn.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            print(f"Error invalidating cache pattern {pattern}: {e}")
            return 0
    
    @staticmethod
    def invalidate_movie(movie_id):
        """
        Invalidate all cache entries related to a specific movie
        """
        patterns = [
            f'movie:{movie_id}:*',
            f'movie_detail:{movie_id}',
            'movie_list:*',
            'recommendations:*',
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += CacheManager.invalidate_pattern(pattern)
        
        return total_deleted
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """
        Invalidate all cache entries related to a specific user
        """
        patterns = [
            f'user:{user_id}:*',
            f'recommendations:user:{user_id}',
            f'ratings:user:{user_id}',
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += CacheManager.invalidate_pattern(pattern)
        
        return total_deleted
    
    @staticmethod
    def get_or_set(key, callback, timeout=60*15):
        """
        Get value from cache or set it using callback function
        
        Usage:
            data = CacheManager.get_or_set(
                'my_expensive_key',
                lambda: expensive_database_query(),
                timeout=60*30
            )
        """
        cached_value = cache.get(key)
        
        if cached_value is not None:
            return cached_value
        
        fresh_value = callback()
        cache.set(key, fresh_value, timeout)
        
        return fresh_value


# Predefined cache key patterns
class CacheKeys:
    """Centralized cache key definitions"""
    
    @staticmethod
    def movie_detail(movie_id):
        return f'movie:detail:{movie_id}'
    
    @staticmethod
    def movie_list(filters_hash):
        return f'movie:list:{filters_hash}'
    
    @staticmethod
    def recommendations(user_id):
        return f'recommendations:user:{user_id}'
    
    @staticmethod
    def user_ratings(user_id):
        return f'ratings:user:{user_id}'
    
    @staticmethod
    def trending_movies():
        return 'movies:trending'
    
    @staticmethod
    def top_rated_movies():
        return 'movies:top_rated'