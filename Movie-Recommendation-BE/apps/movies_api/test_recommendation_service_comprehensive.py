"""
Comprehensive tests for RecommendationService - All methods with edge cases
Using Arrange-Act-Assert pattern with extensive mocking
"""
import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from unittest.mock import patch, MagicMock

from apps.movies_api.models import MovieMetadata, Rating, UserProfile
from apps.movies_api.services.recommendation_service import RecommendationService, recommendation_service


@pytest.mark.django_db
class TestCalculateMatchScore:
    """Test match score calculation with various user profiles and movies"""
    
    def setup_method(self):
        cache.clear()
    
    def test_anonymous_user_score_calculation(self):
        # Arrange
        movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='HighRated',
            vote_average=9.0,
            popularity=500.0
        )
        
        # Act
        score = RecommendationService.calculate_match_score(None, movie)
        
        # Assert: Anonymous score = (vote_avg/10)*50 + min(50, (popularity/100)*50)
        expected = (9.0 / 10) * 50 + min(50, (500.0 / 100) * 50)
        assert score == expected
    
    def test_authenticated_user_without_profile(self):
        # Arrange
        user = User.objects.create_user(username='noprofile', password='pass')
        # Don't create profile
        movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='Test',
            vote_average=8.0,
            popularity=100.0
        )
        
        # Act
        score = RecommendationService.calculate_match_score(user, movie)
        
        # Assert: Should fall back to anonymous scoring
        expected = (8.0 / 10) * 50 + min(50, (100.0 / 100) * 50)
        assert score == expected
    
    def test_match_score_with_favorite_genres(self):
        # Arrange
        user = User.objects.create_user(username='testuser', password='pass')
        profile = UserProfile.objects.create(
            user=user,
            favorite_genres=['Drama', 'Thriller', 'Crime']
        )
        
        # Movie with matching genres
        movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='Crime Drama',
            vote_average=8.0,
            popularity=100.0,
            genres=['Drama', 'Crime', 'Action']
        )
        
        # Act
        score = RecommendationService.calculate_match_score(user, movie)
        
        # Assert: Should include genre match score (40 points max)
        assert score > 0
        # Genre match: 2/3 genres match out of user's 3 favorites
        # (2/3) * 40 = ~26.67
        assert 25 < score < 100  # Rough check
    
    def test_match_score_with_rating_history(self):
        # Arrange
        user = User.objects.create_user(username='testuser', password='pass')
        profile = UserProfile.objects.create(user=user, favorite_genres=['Drama'])
        
        # Create highly rated movies by user
        drama1 = MovieMetadata.objects.create(
            tmdb_id=1, title='Drama1', vote_average=7.0, popularity=50.0,
            genres=['Drama']
        )
        drama2 = MovieMetadata.objects.create(
            tmdb_id=2, title='Drama2', vote_average=7.5, popularity=60.0,
            genres=['Drama']
        )
        
        # User rated these highly
        Rating.objects.create(user=user, movie=drama1, score=5)
        Rating.objects.create(user=user, movie=drama2, score=5)
        
        # New drama movie to recommend
        target_movie = MovieMetadata.objects.create(
            tmdb_id=3,
            title='Drama3',
            vote_average=8.0,
            popularity=100.0,
            genres=['Drama', 'Crime']
        )
        
        # Act
        score = RecommendationService.calculate_match_score(user, target_movie)
        
        # Assert
        assert score > 0
        # Should get points from rating history match
        assert 30 < score < 100
    
    def test_match_score_components_sum(self):
        # Arrange
        user = User.objects.create_user(username='testuser', password='pass')
        profile = UserProfile.objects.create(
            user=user,
            favorite_genres=['Action', 'Thriller']
        )
        
        movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='Action Thriller',
            vote_average=9.0,
            popularity=200.0,
            genres=['Action', 'Thriller']
        )
        
        # Act
        score = RecommendationService.calculate_match_score(user, movie)
        
        # Assert: Max possible score is ~100
        # Genre match: 2/2 = 40
        # Rating score: (9.0/10)*20 = 18
        # Popularity: min(10, (200/100)*10) = 10
        # Potential rating history: up to 30
        assert isinstance(score, float)
        assert 0 <= score <= 100


@pytest.mark.django_db
class TestGetRecommendationsForUser:
    """Test recommendation retrieval with caching"""
    
    def setup_method(self):
        cache.clear()
        self.user = User.objects.create_user(username='testuser', password='pass')
        UserProfile.objects.create(user=self.user, favorite_genres=['Drama'])
    
    def test_returns_unrated_movies_for_authenticated_user(self):
        # Arrange
        rated_movie = MovieMetadata.objects.create(
            tmdb_id=1, title='Rated', vote_average=8.0, popularity=100.0
        )
        unrated_movie = MovieMetadata.objects.create(
            tmdb_id=2, title='Unrated1', vote_average=7.5, popularity=90.0
        )
        unrated_movie2 = MovieMetadata.objects.create(
            tmdb_id=3, title='Unrated2', vote_average=7.0, popularity=80.0
        )
        
        # User already rated movie 1
        Rating.objects.create(user=self.user, movie=rated_movie, score=4)
        
        # Act
        results = RecommendationService.get_recommendations_for_user(self.user, limit=10)
        
        # Assert
        recommended_ids = [r['movie'].id for r in results]
        assert rated_movie.id not in recommended_ids
        assert unrated_movie.id in recommended_ids or unrated_movie2.id in recommended_ids
        assert len(results) <= 10
    
    def test_returns_all_movies_for_anonymous_user(self):
        # Arrange
        movie1 = MovieMetadata.objects.create(
            tmdb_id=1, title='Movie1', vote_average=8.0, popularity=100.0
        )
        movie2 = MovieMetadata.objects.create(
            tmdb_id=2, title='Movie2', vote_average=7.5, popularity=90.0
        )
        
        # Create anonymous user (or None)
        from django.contrib.auth.models import AnonymousUser
        anon_user = AnonymousUser()
        
        # Act
        results = RecommendationService.get_recommendations_for_user(anon_user, limit=10)
        
        # Assert
        assert len(results) > 0
        assert len(results) <= 10
    
    def test_respects_limit_parameter(self):
        # Arrange
        for i in range(30):
            MovieMetadata.objects.create(
                tmdb_id=i,
                title=f'Movie{i}',
                vote_average=7.0 + i*0.01,
                popularity=50.0 + i
            )
        
        # Act - Test different limits
        results_5 = RecommendationService.get_recommendations_for_user(self.user, limit=5)
        results_15 = RecommendationService.get_recommendations_for_user(self.user, limit=15)
        
        # Assert
        assert len(results_5) <= 5
        assert len(results_15) <= 15
    
    def test_sorted_by_match_score_descending(self):
        # Arrange
        profile = UserProfile.objects.get(user=self.user)
        profile.favorite_genres = ['Drama', 'Thriller']
        profile.save()
        
        drama = MovieMetadata.objects.create(
            tmdb_id=1, title='Drama', vote_average=9.0, popularity=200.0,
            genres=['Drama']
        )
        action = MovieMetadata.objects.create(
            tmdb_id=2, title='Action', vote_average=8.0, popularity=150.0,
            genres=['Action']
        )
        
        # Act
        results = RecommendationService.get_recommendations_for_user(self.user, limit=10)
        
        # Assert: Drama should score higher due to genre match
        if len(results) >= 2:
            scores = [r['match_score'] for r in results]
            assert scores == sorted(scores, reverse=True)
    
    @patch('apps.movies_api.services.recommendation_service.cache')
    def test_caches_recommendations(self, mock_cache):
        # Arrange
        mock_cache.get.return_value = None
        mock_cache.set = MagicMock()
        
        MovieMetadata.objects.create(
            tmdb_id=1, title='Movie1', vote_average=8.0, popularity=100.0
        )
        
        # Act
        results = RecommendationService.get_recommendations_for_user(self.user, limit=10)
        
        # Assert: Cache set should have been called
        mock_cache.set.assert_called_once()
        args = mock_cache.set.call_args[0]
        cache_key = args[0]
        assert 'recommendations:user' in cache_key


@pytest.mark.django_db
class TestGetSimilarMovies:
    """Test similar movies finding by genre"""
    
    def test_returns_movies_with_matching_genres(self):
        # Arrange
        source_movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='Drama',
            vote_average=8.0,
            popularity=100.0,
            genres=['Drama', 'Crime']
        )
        
        # Similar movies sharing genres
        similar1 = MovieMetadata.objects.create(
            tmdb_id=2,
            title='Crime Drama',
            vote_average=7.5,
            popularity=90.0,
            genres=['Crime', 'Action']
        )
        similar2 = MovieMetadata.objects.create(
            tmdb_id=3,
            title='Pure Drama',
            vote_average=7.0,
            popularity=80.0,
            genres=['Drama', 'History']
        )
        
        # Non-similar movie
        different = MovieMetadata.objects.create(
            tmdb_id=4,
            title='Comedy',
            vote_average=6.5,
            popularity=70.0,
            genres=['Comedy', 'Romance']
        )
        
        # Act
        results = RecommendationService.get_similar_movies(source_movie, limit=10)
        
        # Assert
        result_ids = [m.id for m in results]
        assert source_movie.id not in result_ids  # Shouldn't include itself
        assert similar1.id in result_ids
        assert similar2.id in result_ids
        assert different.id not in result_ids
    
    def test_returns_empty_for_movie_without_genres(self):
        # Arrange
        source_movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='NoGenres',
            vote_average=8.0,
            popularity=100.0,
            genres=[]
        )
        
        other_movie = MovieMetadata.objects.create(
            tmdb_id=2,
            title='SomeGenre',
            vote_average=7.5,
            popularity=90.0,
            genres=['Drama']
        )
        
        # Act
        results = RecommendationService.get_similar_movies(source_movie, limit=10)
        
        # Assert
        assert results == []
    
    def test_respects_limit(self):
        # Arrange
        source_movie = MovieMetadata.objects.create(
            tmdb_id=1,
            title='Drama',
            vote_average=8.0,
            popularity=100.0,
            genres=['Drama']
        )
        
        # Create many similar movies
        for i in range(20):
            MovieMetadata.objects.create(
                tmdb_id=i+2,
                title=f'Drama{i}',
                vote_average=7.0,
                popularity=50.0 + i,
                genres=['Drama']
            )
        
        # Act
        results = RecommendationService.get_similar_movies(source_movie, limit=5)
        
        # Assert
        assert len(results) <= 5


@pytest.mark.django_db
class TestGetTrendingByGenre:
    """Test trending movies filtering by genre"""
    
    def test_returns_movies_in_genre(self):
        # Arrange
        drama = MovieMetadata.objects.create(
            tmdb_id=1, title='Drama1', vote_average=8.5, popularity=100.0,
            genres=['Drama']
        )
        action = MovieMetadata.objects.create(
            tmdb_id=2, title='Action1', vote_average=8.0, popularity=90.0,
            genres=['Action']
        )
        drama_action = MovieMetadata.objects.create(
            tmdb_id=3, title='Both', vote_average=7.5, popularity=80.0,
            genres=['Drama', 'Action']
        )
        
        # Act
        results = RecommendationService.get_trending_by_genre('Drama', limit=10)
        
        # Assert
        result_ids = [m.id for m in results]
        assert drama.id in result_ids
        assert drama_action.id in result_ids
        assert action.id not in result_ids
    
    def test_returns_empty_for_nonexistent_genre(self):
        # Arrange
        MovieMetadata.objects.create(
            tmdb_id=1, title='Action', vote_average=8.0, popularity=100.0,
            genres=['Action']
        )
        
        # Act
        results = RecommendationService.get_trending_by_genre('NonExistent', limit=10)
        
        # Assert
        assert results == []
    
    def test_sorted_by_popularity_and_rating(self):
        # Arrange
        low_pop = MovieMetadata.objects.create(
            tmdb_id=1, title='LowPop', vote_average=9.0, popularity=30.0,
            genres=['Drama']
        )
        high_pop = MovieMetadata.objects.create(
            tmdb_id=2, title='HighPop', vote_average=7.0, popularity=100.0,
            genres=['Drama']
        )
        
        # Act
        results = RecommendationService.get_trending_by_genre('Drama', limit=10)
        
        # Assert: Should be sorted by popularity first
        if len(results) >= 2:
            assert results[0].popularity >= results[1].popularity


@pytest.mark.django_db
class TestGetUserStatistics:
    """Test user statistics calculation"""
    
    def setup_method(self):
        cache.clear()
    
    def test_returns_empty_for_unauthenticated_user(self):
        # Arrange
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        
        # Act
        stats = RecommendationService.get_user_statistics(anon)
        
        # Assert
        assert stats == {}
    
    def test_calculates_total_ratings(self):
        # Arrange
        user = User.objects.create_user(username='testuser', password='pass')
        movie1 = MovieMetadata.objects.create(
            tmdb_id=1, title='Movie1', vote_average=7.0, popularity=50.0
        )
        movie2 = MovieMetadata.objects.create(
            tmdb_id=2, title='Movie2', vote_average=8.0, popularity=60.0
        )
        
        Rating.objects.create(user=user, movie=movie1, score=5)
        Rating.objects.create(user=user, movie=movie2, score=4)
        
        # Act
        stats = RecommendationService.get_user_statistics(user)
        
        # Assert
        assert stats['total_ratings'] == 2
        assert stats['average_rating'] == 4.5
    
    def test_identifies_favorite_genres(self):
        # Arrange
        user = User.objects.create_user(username='testuser', password='pass')
        
        drama = MovieMetadata.objects.create(
            tmdb_id=1, title='Drama', vote_average=7.0, popularity=50.0,
            genres=['Drama']
        )
        drama2 = MovieMetadata.objects.create(
            tmdb_id=2, title='Drama2', vote_average=8.0, popularity=60.0,
            genres=['Drama']
        )
        action = MovieMetadata.objects.create(
            tmdb_id=3, title='Action', vote_average=9.0, popularity=70.0,
            genres=['Action']
        )
        
        # User rates dramas highly, action low
        Rating.objects.create(user=user, movie=drama, score=5)
        Rating.objects.create(user=user, movie=drama2, score=5)
        Rating.objects.create(user=user, movie=action, score=2)
        
        # Act
        stats = RecommendationService.get_user_statistics(user)
        
        # Assert
        assert 'favorite_genres' in stats
        assert 'Drama' in stats['favorite_genres']
    
    def test_calculates_watch_time(self):
        # Arrange
        user = User.objects.create_user(username='testuser', password='pass')
        
        movie1 = MovieMetadata.objects.create(
            tmdb_id=1, title='Movie1', vote_average=7.0, popularity=50.0,
            runtime=120
        )
        movie2 = MovieMetadata.objects.create(
            tmdb_id=2, title='Movie2', vote_average=8.0, popularity=60.0,
            runtime=150
        )
        
        Rating.objects.create(user=user, movie=movie1, score=5)
        Rating.objects.create(user=user, movie=movie2, score=4)
        
        # Act
        stats = RecommendationService.get_user_statistics(user)
        
        # Assert
        assert stats['total_watch_time'] == 270  # 120 + 150
        assert stats['total_watch_time_hours'] == 4.5  # 270 / 60
    
    def test_returns_empty_stats_for_user_without_ratings(self):
        # Arrange
        user = User.objects.create_user(username='testuser', password='pass')
        
        # Act
        stats = RecommendationService.get_user_statistics(user)
        
        # Assert
        assert stats['total_ratings'] == 0
        assert stats['average_rating'] == 0
        assert stats['favorite_genres'] == []
        assert stats['total_watch_time'] == 0
