import requests
import logging
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


def cache_tmdb(ttl: int = 3600):
    """
    Decorator to cache TMDb API responses in Redis.
    Handles Redis connection failures gracefully.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key based on function name and arguments
            # endpoint = args[0] if args else kwargs.get('endpoint', '')
            # params = args[1] if len(args) > 1 else kwargs.get('params', {})
            # Simplified key: tmdb:{func_name}:{args}:{kwargs}
            key_args = ":".join(map(str, args))
            key_kwargs = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"tmdb:{func.__name__}:{key_args}:{key_kwargs}"
            
            try:
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data
            except Exception as e:
                logger.error(f"Redis error (cache.get): {e}")
                # Fallback to direct call
            
            # Cache miss or Redis error
            result = func(self, *args, **kwargs)
            
            if result is not None:
                try:
                    cache.set(cache_key, result, timeout=ttl)
                    logger.debug(f"Cached result for key: {cache_key} (TTL: {ttl})")
                except Exception as e:
                    logger.error(f"Redis error (cache.set): {e}")
            
            return result
        return wrapper
    return decorator


class TMDbService:
    """
    Service class for interacting with The Movie Database (TMDb) API
    """
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
    
    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDb API key not configured. Add TMDB_API_KEY to settings.")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make a request to TMDb API
        
        Args:
            endpoint: API endpoint (e.g., '/movie/popular')
            params: Query parameters
            
        Returns:
            JSON response or None if error
        """
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        try:
            response = requests.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDb API Error for endpoint {endpoint}: {e}")
            return None
    
    @cache_tmdb(ttl=3600)  # 1 hour
    def get_popular_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get popular movies
        """
        return self._make_request('/movie/popular', {'page': page})
    
    @cache_tmdb(ttl=86400)  # 24 hours
    def get_trending_movies(self, time_window: str = 'week') -> Optional[Dict]:
        """
        Get trending movies
        """
        return self._make_request(f'/trending/movie/{time_window}')
    
    @cache_tmdb(ttl=3600)  # 1 hour
    def get_top_rated_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get top rated movies
        """
        return self._make_request('/movie/top_rated', {'page': page})
    
    @cache_tmdb(ttl=1800)  # 30 minutes
    def get_now_playing_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get movies currently in theaters
        """
        return self._make_request('/movie/now_playing', {'page': page})
    
    @cache_tmdb(ttl=7200)  # 2 hours
    def get_upcoming_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get upcoming movies
        """
        return self._make_request('/movie/upcoming', {'page': page})
    
    @cache_tmdb(ttl=604800)  # 1 week (details change rarely)
    def get_movie_details(self, tmdb_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific movie
        """
        return self._make_request(f'/movie/{tmdb_id}')
    
    @cache_tmdb(ttl=1800)  # 30 minutes
    def search_movies(self, query: str, page: int = 1) -> Optional[Dict]:
        """
        Search for movies by title
        """
        return self._make_request('/search/movie', {'query': query, 'page': page})
    
    @cache_tmdb(ttl=3600)  # 1 hour
    def get_movie_by_genre(self, genre_id: int, page: int = 1) -> Optional[Dict]:
        """
        Discover movies by genre
        """
        return self._make_request('/discover/movie', {
            'with_genres': genre_id,
            'page': page,
            'sort_by': 'popularity.desc'
        })
    
    @cache_tmdb(ttl=86400)  # 24 hours (list changes very rarely)
    def get_genres(self) -> Optional[Dict]:
        """
        Get list of official genres
        """
        return self._make_request('/genre/movie/list')
    
    def normalize_movie_data(self, tmdb_movie: Dict) -> Dict:
        """
        Convert TMDb movie data to our database format
        """
        # Parse release date
        release_date = None
        if tmdb_movie.get('release_date'):
            try:
                release_date = datetime.strptime(
                    tmdb_movie['release_date'], 
                    '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        # Get genre names
        genres = []
        if 'genres' in tmdb_movie:
            genres = [g['name'] for g in tmdb_movie['genres']]
        elif 'genre_ids' in tmdb_movie:
            genres = tmdb_movie['genre_ids']
        
        return {
            'tmdb_id': tmdb_movie['id'],
            'title': tmdb_movie.get('title', ''),
            'overview': tmdb_movie.get('overview', ''),
            'release_date': release_date,
            'poster_path': tmdb_movie.get('poster_path', ''),
            'backdrop_path': tmdb_movie.get('backdrop_path', ''),
            'vote_average': tmdb_movie.get('vote_average', 0.0),
            'vote_count': tmdb_movie.get('vote_count', 0),
            'popularity': tmdb_movie.get('popularity', 0.0),
            'genres': genres,
            'runtime': tmdb_movie.get('runtime'),
        }
    
    def get_poster_url(self, poster_path: str, size: str = 'w500') -> str:
        if not poster_path:
            return ''
        return f"{self.IMAGE_BASE_URL}/{size}{poster_path}"
    
    def get_backdrop_url(self, backdrop_path: str, size: str = 'w1280') -> str:
        if not backdrop_path:
            return ''
        return f"{self.IMAGE_BASE_URL}/{size}{backdrop_path}"


# Singleton instance
tmdb_service = TMDbService()
