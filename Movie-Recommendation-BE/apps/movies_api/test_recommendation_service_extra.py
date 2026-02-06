"""
Extra targeted tests for RecommendationService covering uncovered branches
"""
import pytest
from types import SimpleNamespace
from django.core.cache import cache
from apps.movies_api.services.recommendation_service import RecommendationService
from apps.movies_api.models import MovieMetadata, Rating
from django.contrib.auth.models import User
from django.db import IntegrityError


@pytest.mark.django_db
def test_calculate_match_score_profile_missing():
    # Arrange
    # use a simple object to simulate an authenticated user without a profile
    user = SimpleNamespace(is_authenticated=True)
    movie = MovieMetadata.objects.create(tmdb_id=1000, title='NoProfile', vote_average=7.0, popularity=50.0)

    # Act
    score = RecommendationService.calculate_match_score(user, movie)

    # Assert: falls back to anonymous scoring
    anon_score = RecommendationService._anonymous_score(movie)
    assert score == anon_score


@pytest.mark.django_db
def test_calculate_match_score_with_genres_and_history():
    # Arrange
    user = User.objects.create_user(username='huser', password='pass')
    user.profile.favorite_genres = ['Action', 'Thriller']
    user.profile.save()

    m1 = MovieMetadata.objects.create(tmdb_id=2001, title='ActionHigh', genres=['Action'], vote_average=8.0, popularity=80.0)
    m2 = MovieMetadata.objects.create(tmdb_id=2002, title='ActionOther', genres=['Action','Thriller'], vote_average=7.5, popularity=70.0)

    # user rated m1 highly
    Rating.objects.create(user=user, movie=m1, score=5)

    # Act
    score_m1 = RecommendationService.calculate_match_score(user, m1)
    score_m2 = RecommendationService.calculate_match_score(user, m2)

    # Assert: both scores computed and finite
    assert isinstance(score_m1, float)
    assert isinstance(score_m2, float)
    assert score_m2 >= 0


@pytest.mark.django_db
def test_get_recommendations_cache_hit(monkeypatch):
    cache.clear()
    fake = [{'movie': MovieMetadata(id=1, tmdb_id=1, title='X'), 'match_score': 50}]
    monkeypatch.setattr('apps.movies_api.services.recommendation_service.cache.get', lambda k: fake)

    anon = SimpleNamespace(is_authenticated=False)
    res = RecommendationService.get_recommendations_for_user(anon, limit=1)
    assert res == fake


@pytest.mark.django_db
def test_get_recommendations_cache_error(monkeypatch):
    cache.clear()

    def raise_get(k):
        raise Exception('redis down')

    monkeypatch.setattr('apps.movies_api.services.recommendation_service.cache.get', raise_get)

    # create some movies
    for i in range(3):
        MovieMetadata.objects.create(tmdb_id=3000+i, title=f'M{i}', popularity=90-i)

    anon = SimpleNamespace(is_authenticated=False)
    res = RecommendationService.get_recommendations_for_user(anon, limit=2)
    assert isinstance(res, list)
    assert len(res) <= 2


@pytest.mark.django_db
def test_get_similar_movies_no_genres():
    cache.clear()
    movie = MovieMetadata.objects.create(tmdb_id=4000, title='NoGenres', genres=[])
    similar = RecommendationService.get_similar_movies(movie)
    assert similar == []


@pytest.mark.django_db
def test_get_similar_movies_with_overlap():
    cache.clear()
    base = MovieMetadata.objects.create(tmdb_id=4001, title='Base', genres=['A','B'], vote_average=8.0)
    s1 = MovieMetadata.objects.create(tmdb_id=4002, title='S1', genres=['A'], vote_average=7.0)
    s2 = MovieMetadata.objects.create(tmdb_id=4003, title='S2', genres=['B','C'], vote_average=6.5)
    s3 = MovieMetadata.objects.create(tmdb_id=4004, title='S3', genres=['C'], vote_average=9.0)

    res = RecommendationService.get_similar_movies(base, limit=10)
    ids = [m.id for m in res]
    assert s1.id in ids
    assert s2.id in ids
    assert base.id not in ids


@pytest.mark.django_db
def test_get_trending_by_genre_and_caching(monkeypatch):
    cache.clear()
    MovieMetadata.objects.create(tmdb_id=5001, title='Drama1', genres=['Drama'], popularity=90.0)
    MovieMetadata.objects.create(tmdb_id=5002, title='Drama2', genres=['Drama'], popularity=80.0)

    # First call should compute and cache
    res1 = RecommendationService.get_trending_by_genre('Drama', limit=5)
    assert isinstance(res1, list)

    # Force cache.get to return res1 and ensure function returns cached
    monkeypatch.setattr('apps.movies_api.services.recommendation_service.cache.get', lambda k: res1)
    res2 = RecommendationService.get_trending_by_genre('Drama', limit=5)
    assert res2 == res1


@pytest.mark.django_db
def test_get_user_statistics_no_ratings():
    cache.clear()
    user = User.objects.create_user(username='statuser', password='pass')

    stats = RecommendationService.get_user_statistics(user)
    assert isinstance(stats, dict)
    assert stats.get('total_ratings') == 0


@pytest.mark.django_db
def test_get_user_statistics_with_ratings():
    cache.clear()
    user = User.objects.create_user(username='statuser2', password='pass')
    m1 = MovieMetadata.objects.create(tmdb_id=6001, title='Good', runtime=120, genres=['Action'])
    m2 = MovieMetadata.objects.create(tmdb_id=6002, title='Bad', runtime=90, genres=['Drama'])

    Rating.objects.create(user=user, movie=m1, score=5)
    Rating.objects.create(user=user, movie=m2, score=1)

    stats = RecommendationService.get_user_statistics(user)
    assert stats['total_ratings'] == 2
    assert 'average_rating' in stats
    assert 'favorite_genres' in stats
    assert 'total_watch_time' in stats
    assert 'highest_rated' in stats and 'lowest_rated' in stats
