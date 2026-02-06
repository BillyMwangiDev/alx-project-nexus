import pytest
from unittest.mock import MagicMock
from apps.movies_api.cache import CacheManager, get_redis_connection
from django.core.cache import cache


def test_get_or_set_locmem():
    cache.clear()
    key = 'test:get_or_set'
    value = CacheManager.get_or_set(key, lambda: {'x': 1}, timeout=10)
    assert value == {'x': 1}

    # Second call should return cached value
    value2 = CacheManager.get_or_set(key, lambda: {'x': 2}, timeout=10)
    assert value2 == {'x': 1}


def test_invalidate_pattern_with_redis(monkeypatch):
    mock_redis = MagicMock()
    mock_redis.keys.return_value = [b'nexus_movie:movie:1:abc', b'nexus_movie:movie:2:def']
    mock_redis.delete.return_value = 2

    monkeypatch.setattr('apps.movies_api.cache.get_redis_connection', lambda alias='default': mock_redis)

    deleted = CacheManager.invalidate_pattern('movie:*')
    assert deleted == 2
    mock_redis.keys.assert_called()


def test_invalidate_pattern_no_redis(monkeypatch):
    monkeypatch.setattr('apps.movies_api.cache.get_redis_connection', lambda alias='default': None)
    deleted = CacheManager.invalidate_pattern('movie:*')
    assert deleted == 0


def test_invalidate_movie_calls_invalidate_pattern(monkeypatch):
    calls = []

    def fake_invalidate(pattern):
        calls.append(pattern)
        return 1

    monkeypatch.setattr('apps.movies_api.cache.CacheManager.invalidate_pattern', staticmethod(fake_invalidate))
    total = CacheManager.invalidate_movie(42)
    # invalidate_movie defines 4 patterns
    assert total == 4
