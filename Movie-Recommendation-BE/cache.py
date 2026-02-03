from functools import wraps
from django.core.cache import cache
from django.conf import settings
from django_redis import get_redis_connection
import hashlib
import json
from typing import Any, Callable, Optional, Set


# ==================== Constants ====================
KEY_PREFIX = getattr(settings, 'CACHES', {}).get('default', {}).get('KEY_PREFIX', 'nexus_movie')


def make_full_key(partial_key: str) -> str:
    """Apply the project's KEY_PREFIX to any partial key"""
    if partial_key.startswith(KEY_PREFIX + ":"):
        return partial_key
    return f"{KEY_PREFIX}:{partial_key}"


def cache_key_generator(*args, **kwargs) -> str:
    """
    Generate a consistent, unique hash from arguments
    """
    key_parts = [str(arg) for arg in args if arg is not None]
    key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()


def cached_view(timeout: int = 60*15, key_prefix: str = 'view'):
    """
    Decorator for caching view responses (including query params and user)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            key_parts = [
                key_prefix,
                func.__name__,
                cache_key_generator(*args, **kwargs),
                cache_key_generator(**dict(request.GET)),
            ]

            if request.user.is_authenticated:
                key_parts.append(f"user:{request.user.id}")

            cache_key = make_full_key(":".join(key_parts))

            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            response = func(request, *args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)

            return response
        return wrapper
    return decorator


def cached_query(timeout: int = 60*15, key_prefix: str = 'query'):
    """
    Decorator for caching function/query results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            partial_key = f"{key_prefix}:{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            cache_key = make_full_key(partial_key)

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)

            return result
        return wrapper
    return decorator


class CacheManager:
    """
    Central place for cache invalidation and utilities
    """

    @staticmethod
    def invalidate_pattern(pattern: str, prefix: bool = True) -> int:
        """
        Delete all keys matching the pattern (using real Redis connection)
        """
        if prefix:
            pattern = make_full_key(pattern)

        try:
            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(pattern)
            if keys:
                redis_conn.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            print(f"Cache invalidation error for pattern '{pattern}': {e}")
            return 0


    @staticmethod
    def invalidate_movie(movie_id: Any) -> int:
        """
        Invalidate all cache entries related to a specific movie
        """
        patterns = [
            f"movie:detail:{movie_id}",
            f"movie:similar:{movie_id}",
            f"movie:avg_rating:{movie_id}",
            f"movie:{movie_id}:*",
            "movie_list:*",               
            "recommendations:*",      
        ]

        total_deleted = 0
        for pattern in patterns:
            total_deleted += CacheManager.invalidate_pattern(pattern)

        return total_deleted


    @staticmethod
    def invalidate_user(user_id: Any) -> int:
        """
        Invalidate cache entries related to a specific user
        """
        patterns = [
            f"user:{user_id}:*",
            f"recommendations:user:{user_id}",
            f"playlist:user:{user_id}",
            f"ratings:user:{user_id}",
        ]

        total_deleted = 0
        for pattern in patterns:
            total_deleted += CacheManager.invalidate_pattern(pattern)

        return total_deleted


    @staticmethod
    def get_or_set(key: str, callback: Callable[[], Any], timeout: int = 60*15) -> Any:
        """
        Get from cache or compute and set (non-JSON specific)
        """
        full_key = make_full_key(key)
        value = cache.get(full_key)

        if value is not None:
            return value

        fresh_value = callback()
        cache.set(full_key, fresh_value, timeout=timeout)
        return fresh_value


    @staticmethod
    def get_or_set_json(key: str, callback: Callable[[], Any], timeout: int = 60*15) -> Any:
        """
        Same as get_or_set but documents that the value should be JSON-serializable
        """
        return CacheManager.get_or_set(key, callback, timeout)


class CacheKeys:
    """
    Centralized cache key patterns for movies (without prefix)
    Use CacheManager or make_full_key() when needed
    """

    @staticmethod
    def movie_detail(movie_id: Any) -> str:
        return f"movie:detail:{movie_id}"

    @staticmethod
    def movie_similar(movie_id: Any) -> str:
        return f"movie:similar:{movie_id}"

    @staticmethod
    def recommendations(user_id: Any) -> str:
        return f"recommendations:user:{user_id}"

    @staticmethod
    def movie_list(filters_hash: str) -> str:
        return f"movie:list:{filters_hash}"

    @staticmethod
    def genre_movies(genre_id: Any) -> str:
        return f"movie:genre:{genre_id}"

    @staticmethod
    def trending() -> str:
        return "movie:trending"

    @staticmethod
    def popular() -> str:
        return "movie:popular"


# For backward compatibility / tests that use CacheKeys.movie_detail
MovieCacheKeys = CacheKeys


class RedisCacheBackend:
    """
    Direct Redis access for advanced use cases (tags, counters, locks)
    """

    def __init__(self):
        self.cache = cache

    def set_with_tags(self, key: str, value: Any, tags: list[str], timeout: Optional[int] = None):
        full_key = make_full_key(key)
        self.cache.set(full_key, value, timeout=timeout)

        for tag in tags:
            tag_key = make_full_key(f"tag:{tag}")
            tagged_keys = self.cache.get(tag_key) or set()
            tagged_keys.add(full_key)
            self.cache.set(tag_key, tagged_keys, timeout=timeout or 60*60*24)

    def invalidate_by_tag(self, tag: str) -> int:
        tag_key = make_full_key(f"tag:{tag}")
        tagged_keys = self.cache.get(tag_key)

        if not tagged_keys:
            return 0

        count = len(tagged_keys)
        self.cache.delete_many(tagged_keys)
        self.cache.delete(tag_key)
        return count

    def increment_counter(self, key: str, amount: int = 1) -> int:
        full_key = make_full_key(key)
        try:
            return self.cache.incr(full_key, amount)
        except ValueError:
            self.cache.set(full_key, amount)
            return amount


# Singleton
redis_backend = RedisCacheBackend()