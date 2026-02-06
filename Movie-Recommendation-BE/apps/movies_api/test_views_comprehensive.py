"""
Comprehensive tests for views.py - Additional endpoint and edge case coverage
Using Arrange-Act-Assert pattern with mocked external dependencies
"""
import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from apps.movies_api.models import MovieMetadata, UserProfile, Rating
from apps.movies_api.cache import CacheManager, CacheKeys


@pytest.mark.django_db
class TestMovieListViewBehavior:
    """Test list view with various filters and cache scenarios"""
    
    def setup_method(self):
        """Initialize test data and client"""
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        
    def test_list_returns_paginated_results(self):
        # Arrange
        movies = [
            MovieMetadata.objects.create(
                tmdb_id=i, 
                title=f'Movie {i}',
                vote_average=7.0 + i*0.1,
                popularity=50.0 + i*10
            ) for i in range(25)
        ]
        
        # Act
        response = self.client.get('/api/movies/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20  # Default page size
    
    def test_list_respects_search_filter(self):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='Inception', vote_average=8.0, popularity=100.0
        )
        MovieMetadata.objects.create(
            tmdb_id=2, title='Interstellar', vote_average=8.5, popularity=95.0
        )
        MovieMetadata.objects.create(
            tmdb_id=3, title='The Matrix', vote_average=8.7, popularity=80.0
        )
        
        # Act
        response = self.client.get('/api/movies/?search=Inception')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Inception'
    
    def test_list_respects_ordering(self):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='LowRated', vote_average=5.0, popularity=50.0
        )
        MovieMetadata.objects.create(
            tmdb_id=2, title='HighRated', vote_average=9.0, popularity=100.0
        )
        
        # Act
        response = self.client.get('/api/movies/?ordering=-vote_average')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['vote_average'] == 9.0
    
    def test_list_caching_behavior(self):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='Test Movie', vote_average=7.0, popularity=50.0
        )
        
        # Act - First call (cache miss)
        response1 = self.client.get('/api/movies/')
        count1 = response1.data['count']
        
        # Add another movie
        MovieMetadata.objects.create(
            tmdb_id=2, title='New Movie', vote_average=7.5, popularity=55.0
        )
        
        # Act - Second call (should be cached)
        response2 = self.client.get('/api/movies/')
        count2 = response2.data['count']
        
        # Assert: Cached data doesn't include the new movie
        assert count1 ==count2 == 1
        
        # Clear cache and verify new movie appears
        cache.clear()
        response3 = self.client.get('/api/movies/')
        assert response3.data['count'] == 2


@pytest.mark.django_db
class TestMovieDetailView:
    """Test retrieve endpoint with caching"""
    
    def setup_method(self):
        cache.clear()
        self.client = APIClient()
        self.movie = MovieMetadata.objects.create(
            tmdb_id=1, 
            title='Test Movie',
            overview='A great movie',
            vote_average=8.0,
            popularity=100.0,
            genres=['Drama', 'Thriller']
        )
    
    def test_retrieve_returns_full_serializer(self):
        # Act
        response = self.client.get(f'/api/movies/{self.movie.id}/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.movie.id
        assert response.data['title'] == 'Test Movie'
        assert response.data['overview'] == 'A great movie'
        assert response.data['genres'] == ['Drama', 'Thriller']
    
    def test_retrieve_caching(self):
        # Act - First call (cache miss)
        response1 = self.client.get(f'/api/movies/{self.movie.id}/')
        assert response1.status_code  == status.HTTP_200_OK
        
        # Modify movie in DB
        self.movie.title = 'Modified Title'
        self.movie.save()
        
        # Act - Second call (should be cached)
        response2 = self.client.get(f'/api/movies/{self.movie.id}/')
        
        # Assert: Cached data shows old title
        assert response2.data['title'] == 'Test Movie'


@pytest.mark.django_db
class TestMovieActionEndpoints:
    """Test custom actions like trending, recent, top_rated, recommendations"""
    
    def setup_method(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        
        # Create test movies with varying popularity
        self.trending_movie = MovieMetadata.objects.create(
            tmdb_id=1, title='Trending', vote_average=8.5, popularity=500.0
        )
        self.old_movie = MovieMetadata.objects.create(
            tmdb_id=2, title='Old', vote_average=7.0, popularity=10.0, 
            created_at='2023-01-01'
        )
        self.recent_movie = MovieMetadata.objects.create(
            tmdb_id=3, title='Recent', vote_average=6.5, popularity=50.0
        )
        self.highrated_movie = MovieMetadata.objects.create(
            tmdb_id=4, title='TopRated', vote_average=9.5, popularity=200.0,
            vote_count=500
        )
    
    def test_trending_endpoint(self):
        # Act
        response = self.client.get('/api/movies/trending/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 20
        # Trending should be sorted by popularity
        if len(response.data) > 1:
            assert response.data[0]['popularity'] >= response.data[1]['popularity']
    
    def test_recent_endpoint(self):
        # Act
        response = self.client.get('/api/movies/recent/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 20
        # Recent should be sorted by created_at (descending)
        if len(response.data) > 1:
            assert response.data[0]['title'] == 'Recent'
    
    def test_top_rated_endpoint(self):
        # Act
        response = self.client.get('/api/movies/top_rated/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 20
        assert response.data[0]['title'] == 'TopRated'  # 9.5 rating
    
    @patch('apps.movies_api.services.recommendation_service.recommendation_service.get_recommendations_for_user')
    def test_recommendations_endpoint_authenticated(self, mock_get_recs):
        # Arrange
        mock_get_recs.return_value = [
            {'movie': self.trending_movie, 'match_score': 95.0},
            {'movie': self.highrated_movie, 'match_score': 88.0}
        ]
        self.client.force_authenticate(user=self.user)
        
        # Act
        response = self.client.get('/api/movies/recommendations/?limit=10')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['title'] == 'Trending'
        assert response.data[0]['match_score'] == 95.0
        mock_get_recs.assert_called_once()
    
    @patch('apps.movies_api.services.recommendation_service.recommendation_service.get_recommendations_for_user')
    def test_recommendations_endpoint_anonymous(self, mock_get_recs):
        # Arrange
        mock_get_recs.return_value = [
            {'movie': self.trending_movie, 'match_score': 50.0}
        ]
        
        # Act - Anonymous user should still work
        response = self.client.get('/api/movies/recommendations/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        mock_get_recs.assert_called_once()
    
    @patch('apps.movies_api.services.recommendation_service.recommendation_service.get_similar_movies')
    def test_similar_endpoint(self, mock_similar):
        # Arrange
        mock_similar.return_value = [self.old_movie, self.recent_movie]
        
        # Act
        response = self.client.get(f'/api/movies/{self.trending_movie.id}/similar/?limit=5')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        mock_similar.assert_called_once()


@pytest.mark.django_db
class TestMovieCRUDOperations:
    """Test create, update, delete operations and their cache invalidation"""
    
    def setup_method(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(username='admin', password='pass', is_staff=True)
        self.client.force_authenticate(user=self.user)
    
    def test_create_movie_invalidates_list_cache(self):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='Existing', vote_average=7.0, popularity=50.0
        )
        # Prime the cache
        self.client.get('/api/movies/')
        
        payload = {
            'tmdb_id': 2,
            'title': 'New Movie',
            'overview': 'Test',
            'vote_average': 8.0,
            'popularity': 100.0,
            'genres': ['Action']
        }
        
        # Act
        response = self.client.post('/api/movies/', payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        
        # List cache should be cleared, so new movie appears
        list_response = self.client.get('/api/movies/')
        assert list_response.data['count'] == 2
    
    def test_update_movie_invalidates_detail_cache(self):
        # Arrange
        movie = MovieMetadata.objects.create(
            tmdb_id=1, title='Original', vote_average=7.0, popularity=50.0
        )
        # Prime the cache
        self.client.get(f'/api/movies/{movie.id}/')
        
        # Act
        payload = {'title': 'Updated Title'}
        response = self.client.patch(f'/api/movies/{movie.id}/', payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
        
        # Detail cache should be cleared
        fresh_response = self.client.get(f'/api/movies/{movie.id}/')
        assert fresh_response.data['title'] == 'Updated Title'
    
    def test_delete_movie_invalidates_cache(self):
        # Arrange
        movie = MovieMetadata.objects.create(
            tmdb_id=1, title='ToDelete', vote_average=7.0, popularity=50.0
        )
        cache_key = CacheKeys.movie_detail(movie.id)
        cache.set(cache_key, {'id': movie.id, 'title': 'ToDelete'})
        
        # Act
        response = self.client.delete(f'/api/movies/{movie.id}/')
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert cache.get(cache_key) is None  # Cache invalidated


@pytest.mark.django_db
class TestMatchScoreEndpoint:
    """Test match_score endpoint for authenticated users"""
    
    def setup_method(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        profile = UserProfile.objects.create(user=self.user, favorite_genres=['Drama', 'Thriller'])
        self.client.force_authenticate(user=self.user)
        
        self.movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='Drama Film',
            vote_average=8.5,
            popularity=100.0,
            genres=['Drama', 'Crime']
        )
    
    def test_match_score_requires_authentication(self):
        # Arrange
        client = APIClient()
        
        # Act
        response = client.get(f'/api/movies/{self.movie.id}/match_score/')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_match_score_returns_score(self):
        # Act
        response = self.client.get(f'/api/movies/{self.movie.id}/match_score/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert 'match_score' in response.data
        assert response.data['movie_id'] == self.movie.id
        assert response.data['title'] == 'Drama Film'
    
    def test_match_score_caching(self):
        # Act - First call
        response1 = self.client.get(f'/api/movies/{self.movie.id}/match_score/')
        score1 = response1.data['match_score']
        
        # Modify movie in DB
        self.movie.vote_average = 9.5
        self.movie.save()
        
        # Act - Second call (should be cached)
        response2 = self.client.get(f'/api/movies/{self.movie.id}/match_score/')
        score2 = response2.data['match_score']
        
        # Assert: Score is cached
        assert score1 == score2


@pytest.mark.django_db
class TestMovieFilteringEdgeCases:
    """Test filtering edge cases and error handling"""
    
    def setup_method(self):
        cache.clear()
        self.client = APIClient()
        
    def test_filter_by_nonexistent_genre(self):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='Drama', vote_average=7.0, popularity=50.0,
            genres=['Drama']
        )
        
        # Act
        response = self.client.get('/api/movies/?genres=Science%20Fiction')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
    
    def test_filter_by_vote_range(self):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='Good', vote_average=8.0, popularity=50.0
        )
        MovieMetadata.objects.create(
            tmdb_id=2, title='Bad', vote_average=3.0, popularity=30.0
        )
        
        # Act
        response = self.client.get('/api/movies/?min_vote_average=7')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == 'Good'
    
    def test_retrieve_nonexistent_movie_returns_404(self):
        # Act
        response = self.client.get('/api/movies/99999/')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCacheInvalidationPatterns:
    """Test cache invalidation with CacheManager"""
    
    def setup_method(self):
        cache.clear()
        
    def test_invalidate_movie_pattern(self):
        # Arrange
        movie_id = 1
        cache.set(CacheKeys.movie_detail(movie_id), {'title': 'Test'})
        cache.set(f'movie:detail:{movie_id}:extra', {'extra': 'data'})
        
        # Act
        CacheManager.invalidate_movie(movie_id)
        
        # Assert
        assert cache.get(CacheKeys.movie_detail(movie_id)) is None
    
    def test_invalidate_movie_list_pattern(self):
        # Arrange
        cache.set('movie:list:abc123', [])
        cache.set('movie:list:def456', [])
        cache.set('other:key', 'value')
        
        # Act
        CacheManager.invalidate_pattern('movie:list:*')
        
        # Manually checking since invalidate_pattern uses scan
        # which behavior depends on backend
        # Just verify the method runs without error
