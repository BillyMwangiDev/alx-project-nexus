from celery import shared_task
from django.core.cache import cache
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
import requests
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_popular_movies_task(self):
    """
    Fetch and sync popular movies from TMDb API
    """
    from movies.models import Movie, Genre
    from django.conf import settings
    
    try:
        url = f"{settings.TMDB_BASE_URL}/movie/popular"
        params = {
            'api_key': settings.TMDB_API_KEY,
            'page': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        movies_synced = 0
        for movie_data in data.get('results', [])[:20]:  # Sync top 20
            movie, created = Movie.objects.update_or_create(
                tmdb_id=movie_data['id'],
                defaults={
                    'title': movie_data.get('title', ''),
                    'overview': movie_data.get('overview', ''),
                    'release_date': movie_data.get('release_date'),
                    'poster_path': movie_data.get('poster_path'),
                    'backdrop_path': movie_data.get('backdrop_path'),
                    'vote_average': movie_data.get('vote_average', 0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0),
                }
            )
            
            # Sync genres
            genre_ids = movie_data.get('genre_ids', [])
            if genre_ids:
                genres = Genre.objects.filter(tmdb_id__in=genre_ids)
                movie.genres.set(genres)
            
            movies_synced += 1
        
        logger.info(f"Successfully synced {movies_synced} popular movies")
        return f"Synced {movies_synced} movies"
        
    except Exception as exc:
        logger.error(f"Error syncing popular movies: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry after 5 minutes


@shared_task(bind=True, max_retries=3)
def sync_trending_movies_task(self):
    """
    Fetch and sync trending movies from TMDb API
    """
    from movies.models import Movie, Genre
    from django.conf import settings
    
    try:
        url = f"{settings.TMDB_BASE_URL}/trending/movie/week"
        params = {
            'api_key': settings.TMDB_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        movies_synced = 0
        for movie_data in data.get('results', [])[:10]:  # Sync top 10 trending
            movie, created = Movie.objects.update_or_create(
                tmdb_id=movie_data['id'],
                defaults={
                    'title': movie_data.get('title', ''),
                    'overview': movie_data.get('overview', ''),
                    'release_date': movie_data.get('release_date'),
                    'poster_path': movie_data.get('poster_path'),
                    'backdrop_path': movie_data.get('backdrop_path'),
                    'vote_average': movie_data.get('vote_average', 0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0),
                }
            )
            movies_synced += 1
        
        logger.info(f"Successfully synced {movies_synced} trending movies")
        return f"Synced {movies_synced} trending movies"
        
    except Exception as exc:
        logger.error(f"Error syncing trending movies: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)


@shared_task(bind=True)
def update_movie_details_task(self, movie_id):
    """
    Update detailed information for a specific movie
    """
    from movies.models import Movie
    from django.conf import settings
    
    try:
        movie = Movie.objects.get(id=movie_id)
        url = f"{settings.TMDB_BASE_URL}/movie/{movie.tmdb_id}"
        params = {
            'api_key': settings.TMDB_API_KEY,
            'append_to_response': 'credits,videos,keywords'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Update movie details
        movie.runtime = data.get('runtime')
        movie.budget = data.get('budget')
        movie.revenue = data.get('revenue')
        movie.tagline = data.get('tagline', '')
        movie.save()
        
        # Clear cache for this movie
        cache_key = f'movie_detail_{movie_id}'
        cache.delete(cache_key)
        
        logger.info(f"Updated details for movie: {movie.title}")
        return f"Updated movie: {movie.title}"
        
    except Movie.DoesNotExist:
        logger.error(f"Movie with id {movie_id} does not exist")
        return f"Movie {movie_id} not found"
    except Exception as exc:
        logger.error(f"Error updating movie {movie_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_cache_task():
    """
    Clean up old cache entries
    """
    try:
        # This is a placeholder - implement based on your cache keys
        patterns = [
            'movie_detail_*',
            'movie_list_*',
            'recommendations_*',
        ]
        
        deleted_count = 0
        for pattern in patterns:
            keys = cache.keys(pattern)
            if keys:
                cache.delete_many(keys)
                deleted_count += len(keys)
        
        logger.info(f"Cleaned up {deleted_count} cache entries")
        return f"Deleted {deleted_count} cache entries"
        
    except Exception as exc:
        logger.error(f"Error cleaning up cache: {exc}")
        return f"Error: {exc}"


@shared_task
def generate_recommendation_reports_task():
    """
    Generate weekly recommendation quality reports
    """
    from movies.models import Rating, Playlist
    
    try:
        last_week = timezone.now() - timedelta(days=7)
        
        # Calculate statistics
        new_ratings = Rating.objects.filter(created_at__gte=last_week).count()
        avg_rating = Rating.objects.filter(
            created_at__gte=last_week
        ).aggregate(Avg('score'))['score__avg'] or 0
        
        new_playlists = Playlist.objects.filter(created_at__gte=last_week).count()
        
        active_users = Rating.objects.filter(
            created_at__gte=last_week
        ).values('user').distinct().count()
        
        report = {
            'period': 'Last 7 days',
            'new_ratings': new_ratings,
            'average_rating': round(avg_rating, 2),
            'new_playlists': new_playlists,
            'active_users': active_users,
            'generated_at': timezone.now().isoformat()
        }
        
        # Cache the report
        cache.set('weekly_report', report, timeout=60*60*24*7)  # 7 days
        
        logger.info(f"Generated weekly report: {report}")
        return report
        
    except Exception as exc:
        logger.error(f"Error generating report: {exc}")
        return f"Error: {exc}"


@shared_task(bind=True, max_retries=3)
def fetch_movie_from_tmdb(self, tmdb_id):
    """
    Fetch a single movie from TMDb and save to database
    """
    from movies.models import Movie, Genre
    from django.conf import settings
    
    try:
        url = f"{settings.TMDB_BASE_URL}/movie/{tmdb_id}"
        params = {
            'api_key': settings.TMDB_API_KEY,
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        movie, created = Movie.objects.update_or_create(
            tmdb_id=tmdb_id,
            defaults={
                'title': data.get('title', ''),
                'overview': data.get('overview', ''),
                'release_date': data.get('release_date'),
                'poster_path': data.get('poster_path'),
                'backdrop_path': data.get('backdrop_path'),
                'vote_average': data.get('vote_average', 0),
                'vote_count': data.get('vote_count', 0),
                'popularity': data.get('popularity', 0),
                'runtime': data.get('runtime'),
                'budget': data.get('budget'),
                'revenue': data.get('revenue'),
                'tagline': data.get('tagline', ''),
            }
        )
        
        # Sync genres
        genres_data = data.get('genres', [])
        if genres_data:
            for genre_data in genres_data:
                genre, _ = Genre.objects.get_or_create(
                    tmdb_id=genre_data['id'],
                    defaults={'name': genre_data['name']}
                )
                movie.genres.add(genre)
        
        action = 'Created' if created else 'Updated'
        logger.info(f"{action} movie: {movie.title}")
        return f"{action} movie: {movie.title}"
        
    except Exception as exc:
        logger.error(f"Error fetching movie {tmdb_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_recommendation_email(user_id):
    """
    Send personalized movie recommendations to user via email
    (Placeholder - implement with your email service)
    """
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        # Implement email sending logic here
        logger.info(f"Would send recommendations to {user.email}")
        return f"Email sent to {user.email}"
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return f"User {user_id} not found"