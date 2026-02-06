import pytest
from django.contrib.auth.models import User, AnonymousUser
from apps.movies_api.models import MovieMetadata, Rating
from apps.movies_api.services.recommendation_service import RecommendationService


@pytest.mark.django_db
def test_calculate_match_score_anonymous():
    movie = MovieMetadata.objects.create(
        tmdb_id=9001, title="Anon Movie", vote_average=7.0, popularity=50.0
    )
    score = RecommendationService.calculate_match_score(AnonymousUser(), movie)
    assert isinstance(score, float)
    assert score >= 0


@pytest.mark.django_db
def test_calculate_match_score_authenticated():
    user = User.objects.create_user(username='user1', password='pass')
    profile = user.profile
    profile.favorite_genres = ["Action", "Thriller"]
    profile.save()

    movie = MovieMetadata.objects.create(
        tmdb_id=9002, title="Action Movie", genres=["Action"], vote_average=8.0, popularity=80.0
    )

    # Add a high rating by the user on the same movie to exercise rating history logic
    Rating.objects.create(user=user, movie=movie, score=5)

    score = RecommendationService.calculate_match_score(user, movie)
    assert isinstance(score, float)
    assert score >= 0


@pytest.mark.django_db
def test_get_recommendations_for_anonymous_user():
    # create some movies
    for i in range(3):
        MovieMetadata.objects.create(tmdb_id=1000 + i, title=f"M{i}", vote_average=6.0 + i, popularity=10 + i)

    anon = AnonymousUser()
    recs = RecommendationService.get_recommendations_for_user(anon, limit=2)
    assert isinstance(recs, list)
    assert len(recs) <= 2


@pytest.mark.django_db
def test_get_recommendations_for_authenticated_user():
    user = User.objects.create_user(username='recuser', password='pw')
    profile = user.profile
    profile.favorite_genres = ["Drama"]
    profile.save()

    m1 = MovieMetadata.objects.create(tmdb_id=2000, title="Drama One", genres=["Drama"], vote_average=9.0, popularity=90.0)
    m2 = MovieMetadata.objects.create(tmdb_id=2001, title="Other", genres=["Action"], vote_average=5.0, popularity=10.0)

    recs = RecommendationService.get_recommendations_for_user(user, limit=5)
    assert isinstance(recs, list)
    # Each recommendation should be a dict with 'movie' and 'match_score'
    if recs:
        assert 'movie' in recs[0] and 'match_score' in recs[0]
