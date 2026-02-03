from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from apps.movies_api.services.tmdb_service import TMDbService
from apps.movies_api.services.recommendation_service import RecommendationService
from apps.movies_api.models import MovieMetadata
from django.contrib.auth.models import User

class CachingTestCase(TestCase):
    def setUp(self):
        self.tmdb_service = TMDbService()
        self.recommendation_service = RecommendationService()
        cache.clear()

    @patch('apps.movies_api.services.tmdb_service.requests.get')
    def test_tmdb_service_caching(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': [{'id': 1, 'title': 'Cached Movie'}]}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # First call: cache miss
        result1 = self.tmdb_service.get_popular_movies(page=1)
        self.assertEqual(result1['results'][0]['title'], 'Cached Movie')
        self.assertEqual(mock_get.call_count, 1)

        # Second call: cache hit
        result2 = self.tmdb_service.get_popular_movies(page=1)
        self.assertEqual(result2['results'][0]['title'], 'Cached Movie')
        self.assertEqual(mock_get.call_count, 1)  # Should NOT have been called again

    @patch('apps.movies_api.services.tmdb_service.requests.get')
    def test_tmdb_service_graceful_fallback(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': [{'id': 1, 'title': 'Fallback Movie'}]}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Mock cache.get to raise an exception (simulating Redis down)
        with patch('django.core.cache.cache.get', side_effect=Exception("Redis connection error")):
            result = self.tmdb_service.get_popular_movies(page=1)
            self.assertEqual(result['results'][0]['title'], 'Fallback Movie')
            self.assertEqual(mock_get.call_count, 1)

    def test_recommendation_service_caching(self):
        user = User.objects.create_user(username="cachetest", password="password")
        movie = MovieMetadata.objects.create(tmdb_id=999, title="Test Movie", popularity=100)

        # We need to patch the actual recommendation logic to see if it's skipped
        # Or just check if cache.get was called
        with patch('django.core.cache.cache.get') as mock_cache_get:
            mock_cache_get.return_value = [{'movie': movie, 'match_score': 100}]
            
            # This should hit the mock cache and return our mocked result
            results = self.recommendation_service.get_recommendations_for_user(user, limit=1)
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['match_score'], 100)
            mock_cache_get.assert_called_once()

    @patch('apps.movies_api.services.tmdb_service.requests.get')
    def test_different_keys_for_different_params(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': []}
        mock_get.return_value = mock_response

        # Call with page 1
        self.tmdb_service.get_popular_movies(page=1)
        # Call with page 2
        self.tmdb_service.get_popular_movies(page=2)
        
        self.assertEqual(mock_get.call_count, 2)
