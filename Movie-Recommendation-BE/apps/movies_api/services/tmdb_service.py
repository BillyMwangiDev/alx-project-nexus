import requests
from django.conf import settings
from typing import Dict, List, Optional
from datetime import datetime


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
            print(f"TMDb API Error: {e}")
            return None
    
    def get_popular_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get popular movies
        
        Args:
            page: Page number (1-500)
            
        Returns:
            Dictionary with results and pagination info
        """
        return self._make_request('/movie/popular', {'page': page})
    
    def get_trending_movies(self, time_window: str = 'week') -> Optional[Dict]:
        """
        Get trending movies
        
        Args:
            time_window: 'day' or 'week'
            
        Returns:
            Dictionary with trending movies
        """
        return self._make_request(f'/trending/movie/{time_window}')
    
    def get_top_rated_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get top rated movies
        
        Args:
            page: Page number
            
        Returns:
            Dictionary with top rated movies
        """
        return self._make_request('/movie/top_rated', {'page': page})
    
    def get_now_playing_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get movies currently in theaters
        
        Args:
            page: Page number
            
        Returns:
            Dictionary with now playing movies
        """
        return self._make_request('/movie/now_playing', {'page': page})
    
    def get_upcoming_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Get upcoming movies
        
        Args:
            page: Page number
            
        Returns:
            Dictionary with upcoming movies
        """
        return self._make_request('/movie/upcoming', {'page': page})
    
    def get_movie_details(self, tmdb_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific movie
        
        Args:
            tmdb_id: TMDb movie ID
            
        Returns:
            Dictionary with movie details
        """
        return self._make_request(f'/movie/{tmdb_id}')
    
    def search_movies(self, query: str, page: int = 1) -> Optional[Dict]:
        """
        Search for movies by title
        
        Args:
            query: Search query
            page: Page number
            
        Returns:
            Dictionary with search results
        """
        return self._make_request('/search/movie', {'query': query, 'page': page})
    
    def get_movie_by_genre(self, genre_id: int, page: int = 1) -> Optional[Dict]:
        """
        Discover movies by genre
        
        Args:
            genre_id: TMDb genre ID
            page: Page number
            
        Returns:
            Dictionary with movies matching the genre
        """
        return self._make_request('/discover/movie', {
            'with_genres': genre_id,
            'page': page,
            'sort_by': 'popularity.desc'
        })
    
    def get_genres(self) -> Optional[Dict]:
        """
        Get list of official genres
        
        Returns:
            Dictionary with genre list
        """
        return self._make_request('/genre/movie/list')
    
    def normalize_movie_data(self, tmdb_movie: Dict) -> Dict:
        """
        Convert TMDb movie data to our database format
        
        Args:
            tmdb_movie: Raw movie data from TMDb API
            
        Returns:
            Dictionary matching our MovieMetadata model
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
            # Detailed response includes genre objects
            genres = [g['name'] for g in tmdb_movie['genres']]
        elif 'genre_ids' in tmdb_movie:
            # Search/list responses only include IDs
            # You'd need to map these to names using get_genres()
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
        """
        Build full poster URL
        
        Args:
            poster_path: Path from TMDb
            size: Image size (w92, w154, w185, w342, w500, w780, original)
            
        Returns:
            Full URL to poster image
        """
        if not poster_path:
            return ''
        return f"{self.IMAGE_BASE_URL}/{size}{poster_path}"
    
    def get_backdrop_url(self, backdrop_path: str, size: str = 'w1280') -> str:
        """
        Build full backdrop URL
        
        Args:
            backdrop_path: Path from TMDb
            size: Image size (w300, w780, w1280, original)
            
        Returns:
            Full URL to backdrop image
        """
        if not backdrop_path:
            return ''
        return f"{self.IMAGE_BASE_URL}/{size}{backdrop_path}"


# Singleton instance
tmdb_service = TMDbService()