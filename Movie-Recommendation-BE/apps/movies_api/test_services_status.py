import pytest
import redis
from django.conf import settings
from config.celery import app as celery_app

def test_redis_connection():
    """Test if Redis is reachable"""
    try:
        r = redis.Redis(host='127.0.0.1', port=6379, socket_timeout=1)
        assert r.ping() is True
    except Exception as e:
        pytest.skip(f"Redis is not available: {e}")

def test_celery_config():
    """Test if Celery is correctly configured"""
    assert settings.CELERY_BROKER_URL is not None
    assert settings.CELERY_RESULT_BACKEND is not None
    
    # Check if our tasks are registered
    tasks = celery_app.tasks.keys()
    assert 'apps.movies_api.tasks.sync_trending_movies' in tasks

def test_celery_beat_schedule():
    """Test if Celery Beat is correctly configured"""
    from celery.schedules import crontab
    
    schedule = celery_app.conf.beat_schedule
    assert 'sync-trending-movies-daily' in schedule
    assert schedule['sync-trending-movies-daily']['schedule'] == crontab(hour=0, minute=0)
