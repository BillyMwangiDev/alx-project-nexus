import pytest
from unittest.mock import MagicMock, patch
from requests.exceptions import RequestException
from django.core.cache import cache
from apps.movies_api.services.tmdb_service import TMDbService


@pytest.mark.django_db
def test_get_popular_movies_caching(monkeypatch):
    from django.core.cache import cache
    # ensure cache is clear to avoid interference from other tests
    cache.clear()
    mock_get = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {'results': [{'id': 1, 'title': 'Cached Movie'}]}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    with patch('apps.movies_api.services.tmdb_service.requests.get', mock_get):
        svc = TMDbService()
        r1 = svc.get_popular_movies(page=1)
        r2 = svc.get_popular_movies(page=1)

    assert r1['results'][0]['title'] == 'Cached Movie'
    # second call should hit cache, so requests.get called only once
    assert mock_get.call_count == 1


@pytest.mark.django_db
def test_request_exception_returns_none(monkeypatch):
    # ensure no cached responses from other tests interfere
    cache.clear()

    def raise_exc(*args, **kwargs):
        raise RequestException('fail')

    with patch('apps.movies_api.services.tmdb_service.requests.get', side_effect=raise_exc):
        svc = TMDbService()
        res = svc.get_popular_movies(page=1)

    assert res is None


def test_poster_and_backdrop_url_generation():
    svc = TMDbService()
    poster = svc.get_poster_url('/abc.jpg', size='w500')
    backdrop = svc.get_backdrop_url('/bg.jpg', size='w1280')
    assert 'w500' in poster and poster.endswith('/abc.jpg')
    assert 'w1280' in backdrop and backdrop.endswith('/bg.jpg')
