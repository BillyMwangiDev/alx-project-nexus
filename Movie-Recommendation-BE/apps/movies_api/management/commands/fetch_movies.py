import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.movies_api.models import MovieMetadata

class Command(BaseCommand):
    help = 'Fetch live popular movies from TMDB'

    def handle(self, *args, **kwargs):
        self.stdout.write("Connecting to TMDB...")
        
        # 1. Get Genre Mapping (TMDB returns IDs, your model wants Names)
        genre_map = self.get_genre_mapping()
        
        # 2. Fetch Popular Movies (Page 1)
        # You can loop through multiple pages if you want 100+ movies
        url = f"https://api.themoviedb.org/3/movie/popular"
        params = {
            'api_key': settings.TMDB_API_KEY,
            'language': 'en-US',
            'page': 1
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR(f"Failed to fetch data: {response.status_code}"))
            return

        movies = response.json().get('results', [])
        
        for movie_data in movies:
            # Map genre IDs to Names: [28, 12] -> ["Action", "Adventure"]
            genre_names = [genre_map.get(gid) for gid in movie_data.get('genre_ids', []) if gid in genre_map]

            # Update or create the movie record
            movie, created = MovieMetadata.objects.update_or_create(
                tmdb_id=movie_data['id'],
                defaults={
                    'title': movie_data['title'],
                    'overview': movie_data['overview'],
                    'release_date': movie_data.get('release_date') or None,
                    'poster_path': movie_data.get('poster_path', ''),
                    'backdrop_path': movie_data.get('backdrop_path', ''),
                    'vote_average': movie_data.get('vote_average', 0.0),
                    'vote_count': movie_data.get('vote_count', 0),
                    'popularity': movie_data.get('popularity', 0.0),
                    'genres': genre_names,  # Saves as a list in your JSONField
                }
            )
            
            status = "Created" if created else "Updated"
            self.stdout.write(f"{status}: {movie.title}")

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {len(movies)} movies."))

    def get_genre_mapping(self):
        """Fetches the genre list from TMDB to create an ID -> Name map."""
        url = f"https://api.themoviedb.org/3/genre/movie/list"
        params = {'api_key': settings.TMDB_API_KEY, 'language': 'en-US'}
        res = requests.get(url, params=params).json()
        return {g['id']: g['name'] for g in res.get('genres', [])}