import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.movies_api.models import MovieMetadata


@pytest.mark.django_db
def test_movie_list_and_detail_endpoints():
    client = APIClient()
    m = MovieMetadata.objects.create(tmdb_id=3000, title='List Movie', vote_average=7.0)

    res = client.get('/api/movies/')
    assert res.status_code == 200
    assert 'results' in res.data

    res2 = client.get(f'/api/movies/{m.id}/')
    assert res2.status_code == 200
    assert res2.data['title'] == 'List Movie'


@pytest.mark.django_db
def test_recommendations_endpoint_anonymous_and_authenticated():
    client = APIClient()
    # anonymous request should return 200 (generic recommendations)
    r = client.get('/api/movies/recommendations/')
    assert r.status_code == 200

    # authenticated request
    user = User.objects.create_user(username='viewuser', password='pw')
    client.force_authenticate(user=user)
    r2 = client.get('/api/movies/recommendations/')
    assert r2.status_code == 200
