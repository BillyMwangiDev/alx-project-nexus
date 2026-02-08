import requests
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.movies_api.models import MovieMetadata

class Command(BaseCommand):
    help = 'Fetch live popular movies from TMDB and update MovieMetadata'

    def handle(self, *args, **kwargs):
        # 1. Fail-fast check for API Key
        api_key = getattr(settings, 'TMDB_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.WARNING(
                "SKIPPING FETCH: TMDB_API_KEY is not set in environment variables."
            ))
            return

        self.stdout.write("Connecting to TMDB...")
        
        # 2. Get Genre Mapping
        genre_map = self.get_genre_mapping(api_key)
        
        count_created = 0
        count_updated = 0

        # 3. Fetch Multiple Pages (5 pages = 100 movies)
        # We use a loop to iterate through pages
        for page in range(1, 6):
            self.stdout.write(f"Fetching page {page}...")
            url = f"{settings.TMDB_BASE_URL}/movie/popular"
            params = {
                'api_key': api_key,
                'language': 'en-US',
                'page': page
            }
            
            try:
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code != 200:
                    self.stdout.write(self.style.ERROR(
                        f"TMDB API Error on page {page}: Received status code {response.status_code}"
                    ))
                    break # Stop if we hit an error

                data = response.json()
                movies_data = data.get('results', [])
                
                for movie in movies_data:
                    # Map genre IDs to Names
                    genre_names = [
                        genre_map.get(gid) for gid in movie.get('genre_ids', []) 
                        if genre_map.get(gid)
                    ]

                    obj, created = MovieMetadata.objects.update_or_create(
                        tmdb_id=movie['id'],
                        defaults={
                            'title': movie['title'],
                            'overview': movie['overview'],
                            'release_date': movie.get('release_date') or None,
                            'poster_path': movie.get('poster_path', ''),
                            'backdrop_path': movie.get('backdrop_path', ''),
                            'vote_average': movie.get('vote_average', 0.0),
                            'vote_count': movie.get('vote_count', 0),
                            'popularity': movie.get('popularity', 0.0),
                            'genres': genre_names,
                        }
                    )
                    
                    if created:
                        count_created += 1
                    else:
                        count_updated += 1
                
                # Small pause to avoid hitting rate limits too hard
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Network error on page {page}: {e}"))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Unexpected error on page {page}: {e}"))
                break

        self.stdout.write(self.style.SUCCESS(
            f"Sync Complete: {count_created} new movies added, {count_updated} movies updated."
        ))

    def get_genre_mapping(self, api_key):
        """Helper to get {id: 'Name'} mapping from TMDB with safety checks."""
        url = f"{settings.TMDB_BASE_URL}/genre/movie/list"
        try:
            res = requests.get(url, params={'api_key': api_key}, timeout=10)
            if res.status_code == 200:
                genres = res.json().get('genres', [])
                return {g['id']: g['name'] for g in genres}
            else:
                self.stdout.write(self.style.WARNING(
                    f"Could not fetch genre list (Status {res.status_code}). Genres will be empty."
                ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Genre fetch failed: {e}"))
        
        return {}