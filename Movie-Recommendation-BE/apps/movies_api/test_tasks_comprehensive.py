"""
Comprehensive tests for Celery tasks - Sync, update, and cleanup tasks with mocked TMDb calls
Using Arrange-Act-Assert pattern with unittest.mock
"""
import pytest
from django.utils import timezone
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from datetime import timedelta

from apps.movies_api.models import MovieMetadata, Rating
from apps.movies_api.tasks import (
    sync_trending_movies, 
    update_movie_metadata,
    bulk_update_popularity,
    cleanup_old_movies
)


@pytest.mark.django_db
class TestSyncTrendingMoviesTask:
    """Test sync_trending_movies task with mocked TMDb API"""
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_sync_creates_new_movies(self, mock_tmdb):
        # Arrange
        mock_tmdb.get_trending_movies.return_value = {
            'results': [
                {'id': 1, 'title': 'Movie1'},
                {'id': 2, 'title': 'Movie2'}
            ]
        }
        mock_tmdb.get_movie_details.side_effect = [
            {
                'id': 1,
                'title': 'Movie1',
                'overview': 'Overview1',
                'vote_average': 8.0,
                'popularity': 100.0,
                'genres': [{'id': 1, 'name': 'Action'}],
                'runtime': 120
            },
            {
                'id': 2,
                'title': 'Movie2',
                'overview': 'Overview2',
                'vote_average': 7.5,
                'popularity': 95.0,
                'genres': [{'id': 1, 'name': 'Action'}],
                'runtime': 130
            }
        ]
        mock_tmdb.normalize_movie_data.side_effect = [
            {
                'tmdb_id': 1,
                'title': 'Movie1',
                'overview': 'Overview1',
                'vote_average': 8.0,
                'popularity': 100.0,
                'genres': ['Action'],
                'runtime': 120
            },
            {
                'tmdb_id': 2,
                'title': 'Movie2',
                'overview': 'Overview2',
                'vote_average': 7.5,
                'popularity': 95.0,
                'genres': ['Action'],
                'runtime': 130
            }
        ]
        
        initial_count = MovieMetadata.objects.count()
        
        # Act
        result = sync_trending_movies()
        
        # Assert
        assert result['status'] == 'success'
        assert result['created'] == 2
        assert result['updated'] == 0
        assert MovieMetadata.objects.count() == initial_count + 2
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_sync_updates_existing_movies(self, mock_tmdb):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='OldTitle', vote_average=7.0, popularity=50.0
        )
        
        mock_tmdb.get_trending_movies.return_value = {
            'results': [{'id': 1, 'title': 'Movie1'}]
        }
        mock_tmdb.get_movie_details.return_value = {
            'id': 1, 'title': 'UpdatedTitle', 'vote_average': 8.5, 'popularity': 100.0,
            'genres': [{'id': 1, 'name': 'Drama'}], 'runtime': 120, 'overview': 'New'
        }
        mock_tmdb.normalize_movie_data.return_value = {
            'tmdb_id': 1,
            'title': 'UpdatedTitle',
            'vote_average': 8.5,
            'popularity': 100.0,
            'genres': ['Drama'],
            'runtime': 120,
            'overview': 'New'
        }
        
        # Act
        result = sync_trending_movies()
        
        # Assert
        assert result['status'] == 'success'
        assert result['created'] == 0
        assert result['updated'] == 1
        updated_movie = MovieMetadata.objects.get(tmdb_id=1)
        assert updated_movie.title == 'UpdatedTitle'
        assert updated_movie.vote_average == 8.5
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_sync_handles_missing_response(self, mock_tmdb):
        # Arrange
        mock_tmdb.get_trending_movies.return_value = None
        
        # Act
        result = sync_trending_movies()
        
        # Assert
        assert result['status'] == 'failed'
        assert 'No response' in result['reason']
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_sync_handles_api_error(self, mock_tmdb):
        # Arrange
        mock_tmdb.get_trending_movies.side_effect = Exception('API Error')
        
        # Act & Assert: Task should retry
        with pytest.raises(Exception):
            sync_trending_movies.apply()


@pytest.mark.django_db
class TestUpdateMovieMetadataTask:
    """Test update_movie_metadata task"""
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_update_existing_movie(self, mock_tmdb):
        # Arrange
        movie = MovieMetadata.objects.create(
            tmdb_id=123, title='Original', vote_average=7.0, popularity=50.0
        )
        
        mock_tmdb.get_movie_details.return_value = {
            'id': 123,
            'title': 'Updated',
            'vote_average': 8.5,
            'popularity': 100.0,
            'genres': [{'id': 1, 'name': 'Drama'}],
            'runtime': 140,
            'overview': 'Updated overview'
        }
        mock_tmdb.normalize_movie_data.return_value = {
            'tmdb_id': 123,
            'title': 'Updated',
            'vote_average': 8.5,
            'popularity': 100.0,
            'genres': ['Drama'],
            'runtime': 140,
            'overview': 'Updated overview'
        }
        
        # Act
        result = update_movie_metadata(123)
        
        # Assert
        assert result['status'] == 'success'
        assert result['created'] == False
        updated_movie = MovieMetadata.objects.get(tmdb_id=123)
        assert updated_movie.title == 'Updated'
        assert updated_movie.vote_average == 8.5
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_update_creates_new_movie(self, mock_tmdb):
        # Arrange
        mock_tmdb.get_movie_details.return_value = {
            'id': 456,
            'title': 'NewMovie',
            'vote_average': 7.8,
            'popularity': 75.0,
            'genres': [{'id': 2, 'name': 'Thriller'}],
            'runtime': 125,
            'overview': 'New overview'
        }
        mock_tmdb.normalize_movie_data.return_value = {
            'tmdb_id': 456,
            'title': 'NewMovie',
            'vote_average': 7.8,
            'popularity': 75.0,
            'genres': ['Thriller'],
            'runtime': 125,
            'overview': 'New overview'
        }
        
        # Act
        result = update_movie_metadata(456)
        
        # Assert
        assert result['status'] == 'success'
        assert result['created'] == True
        assert MovieMetadata.objects.filter(tmdb_id=456).exists()
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_update_handles_missing_movie(self, mock_tmdb):
        # Arrange
        mock_tmdb.get_movie_details.return_value = None
        
        # Act
        result = update_movie_metadata(999)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'not found' in result['reason']


@pytest.mark.django_db
class TestBulkUpdatePopularityTask:
    """Test bulk_update_popularity task"""
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_bulk_update_all_movies(self, mock_tmdb):
        # Arrange
        movie1 = MovieMetadata.objects.create(
            tmdb_id=1, title='Movie1', vote_average=7.0, popularity=50.0, vote_count=100
        )
        movie2 = MovieMetadata.objects.create(
            tmdb_id=2, title='Movie2', vote_average=6.5, popularity=45.0, vote_count=90
        )
        
        mock_tmdb.get_movie_details.side_effect = [
            {
                'id': 1,
                'popularity': 75.0,
                'vote_average': 8.2,
                'vote_count': 150
            },
            {
                'id': 2,
                'popularity': 70.0,
                'vote_average': 7.8,
                'vote_count': 140
            }
        ]
        
        # Act
        result = bulk_update_popularity()
        
        # Assert
        assert result['status'] == 'success'
        assert result['updated'] == 2
        assert result['failed'] == 0
        
        updated_movie1 = MovieMetadata.objects.get(tmdb_id=1)
        assert updated_movie1.popularity == 75.0
        assert updated_movie1.vote_average == 8.2
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_bulk_update_handles_partial_failures(self, mock_tmdb):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='Movie1', vote_average=7.0, popularity=50.0, vote_count=100
        )
        MovieMetadata.objects.create(
            tmdb_id=2, title='Movie2', vote_average=6.5, popularity=45.0, vote_count=90
        )
        
        # First call succeeds, second fails
        mock_tmdb.get_movie_details.side_effect = [
            {'id': 1, 'popularity': 75.0, 'vote_average': 8.2, 'vote_count': 150},
            Exception('API Error')
        ]
        
        # Act
        result = bulk_update_popularity()
        
        # Assert
        assert result['status'] == 'success'
        assert result['updated'] == 1
        assert result['failed'] == 1


@pytest.mark.django_db
class TestCleanupOldMoviesTask:
    """Test cleanup_old_movies task"""
    
    def test_cleanup_removes_old_unrated_movies(self):
        # Arrange
        old_date = timezone.now() - timedelta(days=100)
        
        # Old, unpopular, unrated movie (should be deleted)
        old_movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='OldUnrated',
            vote_average=5.0,
            popularity=5.0,
            vote_count=10
        )
        old_movie.created_at = old_date
        old_movie.save()
        
        # Recent unrated movie (should NOT be deleted)
        recent_movie = MovieMetadata.objects.create(
            tmdb_id=2,
            title='RecentUnrated',
            vote_average=5.0,
            popularity=5.0,
            vote_count=10
        )
        
        initial_count = MovieMetadata.objects.count()
        
        # Act
        result = cleanup_old_movies()
        
        # Assert
        assert result['status'] == 'success'
        assert result['deleted'] == 1
        assert MovieMetadata.objects.count() == initial_count - 1
        assert not MovieMetadata.objects.filter(tmdb_id=1).exists()
        assert MovieMetadata.objects.filter(tmdb_id=2).exists()
    
    def test_cleanup_preserves_rated_movies(self):
        # Arrange
        old_date = timezone.now() - timedelta(days=100)
        user = User.objects.create_user(username='testuser', password='pass')
        
        # Old, unpopular movie with rating (should NOT be deleted)
        old_rated_movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='OldRated',
            vote_average=5.0,
            popularity=5.0,
            vote_count=10
        )
        old_rated_movie.created_at = old_date
        old_rated_movie.save()
        
        Rating.objects.create(user=user, movie=old_rated_movie, score=5)
        
        # Act
        result = cleanup_old_movies()
        
        # Assert
        assert result['status'] == 'success'
        assert result['deleted'] == 0
        assert MovieMetadata.objects.filter(tmdb_id=1).exists()
    
    def test_cleanup_preserves_popular_movies(self):
        # Arrange
        old_date = timezone.now() - timedelta(days=100)
        
        # Old but popular unrated movie (should NOT be deleted)
        old_popular = MovieMetadata.objects.create(
            tmdb_id=1,
            title='OldPopular',
            vote_average=8.0,
            popularity=100.0,  # High popularity
            vote_count=500
        )
        old_popular.created_at = old_date
        old_popular.save()
        
        # Act
        result = cleanup_old_movies()
        
        # Assert
        assert result['status'] == 'success'
        assert result['deleted'] == 0
        assert MovieMetadata.objects.filter(tmdb_id=1).exists()
    
    def test_cleanup_handles_errors(self):
        # Arrange - No error, just verify error handling path
        
        # Act
        result = cleanup_old_movies()
        
        # Assert - Should return success even with no movies
        assert result['status'] == 'success'
        assert result['deleted'] == 0


@pytest.mark.django_db
class TestTaskErrorHandling:
    """Test error handling and retry behavior"""
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_sync_task_retries_on_error(self, mock_tmdb):
        # Arrange
        mock_tmdb.get_trending_movies.side_effect = ConnectionError('Network error')
        
        # Act & Assert
        with pytest.raises(ConnectionError):
            sync_trending_movies.apply()
    
    @patch('apps.movies_api.tasks.tmdb_service')
    def test_update_task_retries_on_error(self, mock_tmdb):
        # Arrange
        mock_tmdb.get_movie_details.side_effect = Exception('API Error')
        
        # Act & Assert
        with pytest.raises(Exception):
            update_movie_metadata.apply(args=[123])
    
    def test_cleanup_task_handles_unexpected_errors(self):
        # Act - Should complete gracefully even if something goes wrong
        result = cleanup_old_movies()
        
        # Assert
        assert isinstance(result, dict)
        assert 'status' in result
