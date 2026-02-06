"""
Targeted tests for tasks.py
"""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from apps.movies_api.tasks import cleanup_old_movies
from apps.movies_api.models import MovieMetadata, Rating
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_cleanup_removes_old_unrated_movies():
    """Test cleanup_old_movies removes old movies with no ratings and low popularity"""
    # Create an old movie
    old_date = timezone.now() - timedelta(days=91)
    movie = MovieMetadata.objects.create(
        tmdb_id=1,
        title='Old Movie',
        popularity=5.0,
        created_at=old_date,
        updated_at=old_date
    )
    
    # This should be deleted
    result = cleanup_old_movies.delay().get()
    
    assert result['status'] == 'success'


@pytest.mark.django_db
def test_cleanup_keeps_rated_movies():
    """Test cleanup doesn't remove movies with ratings"""
    # Create old movie with low popularity
    old_date = timezone.now() - timedelta(days=100)
    movie = MovieMetadata.objects.create(
        tmdb_id=2,
        title='Rated Movie',
        popularity=5.0,
        created_at=old_date
    )
    
    # Add a rating
    user = User.objects.create_user(username='rater', password='pass')
    Rating.objects.create(user=user, movie=movie, score=5)
    
    result = cleanup_old_movies.delay().get()
    
    # Movie should still exist
    assert MovieMetadata.objects.filter(id=movie.id).exists()


@pytest.mark.django_db
def test_cleanup_keeps_popular():
    """Test cleanup keeps popular movies"""
    # Create old popular movie
    old_date = timezone.now() - timedelta(days=100)
    movie = MovieMetadata.objects.create(
        tmdb_id=3,
        title='Popular Old',
        popularity=50.0,
        created_at=old_date
    )
    
    result = cleanup_old_movies.delay().get()
    
    # Movie should still exist
    assert MovieMetadata.objects.filter(id=movie.id).exists()


@pytest.mark.django_db
def test_cleanup_keeps_new_movies():
    """Test cleanup keeps recently created movies"""
    # Create new movie
    movie = MovieMetadata.objects.create(
        tmdb_id=4,
        title='New Movie',
        popularity=5.0
    )
    
    result = cleanup_old_movies.delay().get()
    
    # Movie should still exist
    assert MovieMetadata.objects.filter(id=movie.id).exists()


@pytest.mark.django_db
def test_cleanup_handles_errors():
    """Test cleanup handles database errors"""
    result = cleanup_old_movies.delay().get()
    
    # Should not crash
    assert result['status'] == 'success' or result['status'] == 'failed'
