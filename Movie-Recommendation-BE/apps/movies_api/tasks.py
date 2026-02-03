"""
Celery tasks for background processing
Run with: celery -A config worker -l info
"""
from celery import shared_task
from django.utils import timezone
from apps.movies_api.models import MovieMetadata
from apps.movies_api.services.tmdb_service import tmdb_service
import logging
import time

logger = logging.getLogger(__name__)


@shared_task(
    bind=True, 
    max_retries=3, 
    default_retry_delay=60,
    retry_backoff=True
)
def sync_trending_movies(self):
    """
    Sync trending movies from TMDb
    Run this daily to keep trending movies updated
    """
    logger.info("Starting trending movies sync...")
    
    try:
        response = tmdb_service.get_trending_movies('week')
        
        if not response or 'results' not in response:
            logger.error("Failed to fetch trending movies: No response from TMDb")
            return {'status': 'failed', 'reason': 'No response from TMDb'}
        
        movies = response['results']
        created_count = 0
        updated_count = 0
        
        for tmdb_movie in movies:
            try:
                # Get detailed movie info
                movie_details = tmdb_service.get_movie_details(tmdb_movie['id'])
                
                if not movie_details:
                    continue
                
                # Normalize the data
                movie_data = tmdb_service.normalize_movie_data(movie_details)
                
                # Create or update in database
                movie, created = MovieMetadata.objects.update_or_create(
                    tmdb_id=movie_data['tmdb_id'],
                    defaults=movie_data
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
                # Small delay to respect rate limits (even with caching)
                time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error processing movie {tmdb_movie.get('id')}: {str(e)}")
                continue
        
        result = {
            'status': 'success',
            'created': created_count,
            'updated': updated_count,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Sync complete: {result}")
        return result

    except Exception as exc:
        logger.error(f"Error in sync_trending_movies task: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def update_movie_metadata(self, tmdb_id):
    """
    Update metadata for a specific movie from TMDb
    """
    try:
        movie_details = tmdb_service.get_movie_details(tmdb_id)
        
        if not movie_details:
            return {'status': 'failed', 'reason': 'Movie not found on TMDb'}
        
        movie_data = tmdb_service.normalize_movie_data(movie_details)
        
        movie, created = MovieMetadata.objects.update_or_create(
            tmdb_id=movie_data['tmdb_id'],
            defaults=movie_data
        )
        
        return {
            'status': 'success',
            'movie_id': movie.id,
            'tmdb_id': tmdb_id,
            'created': created,
            'title': movie.title
        }
    
    except Exception as exc:
        logger.error(f"Error updating movie {tmdb_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, retry_backoff=True)
def bulk_update_popularity(self):
    """
    Update popularity scores for all movies in database
    """
    logger.info("Starting bulk popularity update...")
    
    try:
        movies = MovieMetadata.objects.all()
        updated_count = 0
        failed_count = 0
        
        for movie in movies:
            try:
                movie_details = tmdb_service.get_movie_details(movie.tmdb_id)
                
                if movie_details:
                    movie.popularity = movie_details.get('popularity', movie.popularity)
                    movie.vote_average = movie_details.get('vote_average', movie.vote_average)
                    movie.vote_count = movie_details.get('vote_count', movie.vote_count)
                    movie.save(update_fields=['popularity', 'vote_average', 'vote_count', 'updated_at'])
                    
                    updated_count += 1
                
                time.sleep(0.1)
            
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to update {movie.title}: {str(e)}")
                continue
        
        return {
            'status': 'success',
            'updated': updated_count,
            'failed': failed_count,
            'timestamp': timezone.now().isoformat()
        }
    except Exception as exc:
        logger.error(f"Error in bulk_update_popularity: {exc}")
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_movies():
    """
    Remove movies that haven't been rated and have low popularity
    """
    try:
        from apps.movies_api.models import Rating
        
        threshold_date = timezone.now() - timezone.timedelta(days=90)
        
        old_unrated_movies = MovieMetadata.objects.filter(
            created_at__lt=threshold_date,
            popularity__lt=10
        ).exclude(
            id__in=Rating.objects.values_list('movie_id', flat=True)
        )
        
        count = old_unrated_movies.count()
        old_unrated_movies.delete()
        
        return {
            'status': 'success',
            'deleted': count,
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in cleanup_old_movies: {e}")
        return {'status': 'failed', 'reason': str(e)}
    