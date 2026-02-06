"""
Test settings for Django
Uses SQLite in-memory database instead of PostgreSQL
"""
from .settings import *  # noqa

# Override database to use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Override cache to use local memory for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Ensure tests don't try to connect to real external services
TMDB_API_KEY = 'test_key'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
