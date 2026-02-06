"""
Pytest configuration and fixtures for the project.
"""
import os
import django
from unittest.mock import MagicMock, patch
import pytest

# Set environment variables before any module imports
os.environ.setdefault('TMDB_API_KEY', 'test-api-key-12345')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')


def pytest_configure():
    """Configure Django settings before running tests."""
    django.setup()


@pytest.fixture(autouse=True)
def mock_tmdb_service():
    """
    Automatically mock TMDbService throughout all tests.
    This prevents the actual service from making real API calls.
    """
    mock_service = MagicMock()
    mock_service.get_popular_movies = MagicMock(return_value={'results': []})
    mock_service.get_trending_movies = MagicMock(return_value={'results': []})
    mock_service.get_top_rated_movies = MagicMock(return_value={'results': []})
    mock_service.get_now_playing_movies = MagicMock(return_value={'results': []})
    mock_service.get_upcoming_movies = MagicMock(return_value={'results': []})
    mock_service.get_movie_details = MagicMock(return_value={})
    mock_service.search_movies = MagicMock(return_value={'results': []})
    mock_service.get_movie_by_genre = MagicMock(return_value={'results': []})
    mock_service.get_genres = MagicMock(return_value={'genres': []})
    mock_service.normalize_movie_data = MagicMock(return_value={})
    
    with patch('apps.movies_api.services.tmdb_service.tmdb_service', mock_service):
        with patch('apps.movies_api.tasks.tmdb_service', mock_service):
            yield mock_service


@pytest.fixture(autouse=True)
def mock_tmdb_service():
    """
    Automatically mock TMDbService throughout all tests.
    This prevents the actual service from making real API calls.
    """
    mock_service = MagicMock()
    mock_service.get_popular_movies = MagicMock(return_value={'results': []})
    mock_service.get_trending_movies = MagicMock(return_value={'results': []})
    mock_service.get_top_rated_movies = MagicMock(return_value={'results': []})
    mock_service.get_now_playing_movies = MagicMock(return_value={'results': []})
    mock_service.get_upcoming_movies = MagicMock(return_value={'results': []})
    mock_service.get_movie_details = MagicMock(return_value={})
    mock_service.search_movies = MagicMock(return_value={'results': []})
    mock_service.get_movie_by_genre = MagicMock(return_value={'results': []})
    mock_service.get_genres = MagicMock(return_value={'genres': []})
    mock_service.normalize_movie_data = MagicMock(return_value={})
    
    with patch('apps.movies_api.services.tmdb_service.tmdb_service', mock_service):
        with patch('apps.movies_api.tasks.tmdb_service', mock_service):
            yield mock_service
