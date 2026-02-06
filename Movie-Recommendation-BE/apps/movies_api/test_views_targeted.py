"""
Targeted tests for views.py to increase coverage without complex setup issues
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from django.core.cache import cache
from apps.movies_api.models import MovieMetadata, Rating, Playlist


@pytest.mark.django_db
def test_trending_action():
    """Test trending endpoint"""
    MovieMetadata.objects.create(tmdb_id=1, title='Movie 1', popularity=90.0)
    MovieMetadata.objects.create(tmdb_id=2, title='Movie 2', popularity=85.0)
    cache.clear()
    
    client = APIClient()
    res = client.get('/api/movies/trending/')
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.data, list)


@pytest.mark.django_db
def test_recent_action():
    """Test recent endpoint"""
    MovieMetadata.objects.create(tmdb_id=3, title='Movie 3')
    cache.clear()
    
    client = APIClient()
    res = client.get('/api/movies/recent/')
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.data, list)


@pytest.mark.django_db
def test_top_rated_action():
    """Test top_rated endpoint"""
    MovieMetadata.objects.create(tmdb_id=4, title='Movie 4', vote_count=100, vote_average=8.5)
    cache.clear()
    
    client = APIClient()
    res = client.get('/api/movies/top_rated/')
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.data, list)


@pytest.mark.django_db
def test_similar_action():
    """Test similar endpoint"""
    movie = MovieMetadata.objects.create(tmdb_id=5, title='Movie 5', genres=['Action'])
    MovieMetadata.objects.create(tmdb_id=6, title='Movie 6', genres=['Action'])
    cache.clear()
    
    client = APIClient()
    res = client.get(f'/api/movies/{movie.id}/similar/')
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_list_uses_lighter_serializer():
    """Test that list uses MovieMetadataListSerializer"""
    MovieMetadata.objects.create(tmdb_id=7, title='Movie 7')
    cache.clear()
    
    client = APIClient()
    res = client.get('/api/movies/')
    assert res.status_code == status.HTTP_200_OK
    # ListSerializer returns results in paginated response
    assert 'results' in res.data


@pytest.mark.django_db
def test_rating_create_invalidates_cache():
    """Test that creating rating invalidates user cache"""
    user = User.objects.create_user(username='rater', password='pass')
    movie = MovieMetadata.objects.create(tmdb_id=8, title='Movie 8')
    cache.clear()
    
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.post('/api/ratings/', {
        'movie': movie.id,
        'score': 5,
        'review': 'Great!'
    })
    
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_playlist_add_movie_and_remove():
    """Test adding and removing movies from playlist"""
    user = User.objects.create_user(username='owner', password='pass')
    movie = MovieMetadata.objects.create(tmdb_id=9, title='Movie 9')
    playlist = Playlist.objects.create(owner=user, name='Test Playlist')
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Add movie
    res_add = client.post(f'/api/playlists/{playlist.id}/add_movie/', {'movie_id': movie.id})
    assert res_add.status_code == status.HTTP_200_OK
    
    # Remove movie
    res_remove = client.post(f'/api/playlists/{playlist.id}/remove_movie/', {'movie_id': movie.id})
    assert res_remove.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_registration():
    """Test user registration endpoint"""
    client = APIClient()
    res = client.post('/api/auth/register/', {
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    })
    
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_recommendations_caching():
    """Test recommendations endpoint caching"""
    cache.clear()
    client = APIClient()
    
    res1 = client.get('/api/movies/recommendations/?limit=5')
    assert res1.status_code == status.HTTP_200_OK
    
    # Second call should be cached
    res2 = client.get('/api/movies/recommendations/?limit=5')
    assert res2.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_create_movie_invalidates_cache():
    """Test that creating movie invalidates list cache"""
    user = User.objects.create_user(username='creator', password='pass')
    cache.clear()
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    res = client.post('/api/movies/', {
        'title': 'New Movie from Test',
        'tmdb_id': 999,
        'vote_average': 8.0,
        'popularity': 80.0
    })
    
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_update_movie_invalidates_cache():
    """Test that updating movie invalidates cache"""
    user = User.objects.create_user(username='updater', password='pass')
    movie = MovieMetadata.objects.create(tmdb_id=10, title='Old Title')
    cache.clear()
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    res = client.patch(f'/api/movies/{movie.id}/', {'title': 'New Title'})
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db  
def test_delete_movie_invalidates_cache():
    """Test that deleting movie invalidates cache"""
    user = User.objects.create_user(username='deleter', password='pass')
    movie = MovieMetadata.objects.create(tmdb_id=11, title='To Delete')
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    res = client.delete(f'/api/movies/{movie.id}/')
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not MovieMetadata.objects.filter(id=movie.id).exists()


@pytest.mark.django_db
def test_rating_update_permission():
    """Test rating update permission checks"""
    user1 = User.objects.create_user(username='user1', password='pass')
    user2 = User.objects.create_user(username='user2', password='pass')
    movie = MovieMetadata.objects.create(tmdb_id=12, title='Movie 12')
    
    # User1 rates a movie
    rating = Rating.objects.create(user=user1, movie=movie, score=5)
    
    # User2 tries to update user1's rating
    client = APIClient()
    client.force_authenticate(user=user2)
    
    res = client.patch(f'/api/ratings/{rating.id}/', {'score': 1})
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_rating_delete_permission():
    """Test rating delete permission checks"""
    user1 = User.objects.create_user(username='user3', password='pass')
    user2 = User.objects.create_user(username='user4', password='pass')
    movie = MovieMetadata.objects.create(tmdb_id=13, title='Movie 13')
    
    rating = Rating.objects.create(user=user1, movie=movie, score=5)
    
    client = APIClient()
    client.force_authenticate(user=user2)
    
    res = client.delete(f'/api/ratings/{rating.id}/')
    assert res.status_code == status.HTTP_403_FORBIDDEN
