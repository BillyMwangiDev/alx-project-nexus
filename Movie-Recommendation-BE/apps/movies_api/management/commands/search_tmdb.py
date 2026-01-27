from django.core.management.base import BaseCommand
from apps.movies_api.models import MovieMetadata
from apps.movies_api.services.tmdb_service import tmdb_service


class Command(BaseCommand):
    help = 'Search for movies on TMDb and optionally save them'

    def add_arguments(self, parser):
        parser.add_argument(
            'query',
            type=str,
            help='Search query (movie title)'
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save found movies to database'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of results to process'
        )

    def handle(self, *args, **options):
        query = options['query']
        save = options['save']
        limit = options['limit']
        
        self.stdout.write(f'Searching TMDb for: "{query}"...\n')
        
        # Search movies
        response = tmdb_service.search_movies(query)
        
        if not response or 'results' not in response:
            self.stdout.write(self.style.ERROR('Search failed or no results found'))
            return
        
        results = response['results'][:limit]
        
        if not results:
            self.stdout.write(self.style.WARNING('No movies found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {len(results)} movies:\n'))
        
        saved_count = 0
        
        for idx, movie in enumerate(results, 1):
            title = movie.get('title', 'Unknown')
            year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A'
            rating = movie.get('vote_average', 0)
            
            self.stdout.write(f'{idx}. {title} ({year}) - ⭐ {rating}/10')
            self.stdout.write(f'   ID: {movie["id"]} | Popularity: {movie.get("popularity", 0):.1f}')
            
            if movie.get('overview'):
                overview = movie['overview'][:100] + '...' if len(movie['overview']) > 100 else movie['overview']
                self.stdout.write(f'   {overview}')
            
            self.stdout.write('')
            
            # Save to database if requested
            if save:
                try:
                    # Get detailed info
                    movie_details = tmdb_service.get_movie_details(movie['id'])
                    
                    if movie_details:
                        movie_data = tmdb_service.normalize_movie_data(movie_details)
                        
                        db_movie, created = MovieMetadata.objects.update_or_create(
                            tmdb_id=movie_data['tmdb_id'],
                            defaults=movie_data
                        )
                        
                        if created:
                            saved_count += 1
                            self.stdout.write(self.style.SUCCESS(f'   ✓ Saved to database'))
                        else:
                            self.stdout.write(self.style.WARNING(f'   ↻ Updated in database'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ✗ Failed to save: {str(e)}'))
                
                self.stdout.write('')
        
        if save:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Saved {saved_count} new movies to database'))