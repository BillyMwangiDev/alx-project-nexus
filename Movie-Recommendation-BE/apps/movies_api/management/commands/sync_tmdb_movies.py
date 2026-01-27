from django.core.management.base import BaseCommand
from apps.movies_api.models import MovieMetadata
from apps.movies_api.services.tmdb_service import tmdb_service


class Command(BaseCommand):
    help = 'Sync movies from TMDb API to local database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            default='popular',
            choices=['popular', 'trending', 'top_rated', 'now_playing', 'upcoming'],
            help='Category of movies to fetch'
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Number of pages to fetch (20 movies per page)'
        )

    def handle(self, *args, **options):
        category = options['category']
        pages = options['pages']
        
        self.stdout.write(f'Fetching {category} movies from TMDb API...')
        self.stdout.write(f'Pages to fetch: {pages} (up to {pages * 20} movies)\n')
        
        created_count = 0
        updated_count = 0
        failed_count = 0
        
        for page in range(1, pages + 1):
            self.stdout.write(f'Fetching page {page}...')
            
            # Fetch movies based on category
            if category == 'popular':
                response = tmdb_service.get_popular_movies(page)
            elif category == 'trending':
                response = tmdb_service.get_trending_movies('week')
            elif category == 'top_rated':
                response = tmdb_service.get_top_rated_movies(page)
            elif category == 'now_playing':
                response = tmdb_service.get_now_playing_movies(page)
            elif category == 'upcoming':
                response = tmdb_service.get_upcoming_movies(page)
            
            if not response or 'results' not in response:
                self.stdout.write(self.style.ERROR(f'Failed to fetch page {page}'))
                continue
            
            movies = response['results']
            
            for tmdb_movie in movies:
                try:
                    # Get detailed movie info
                    movie_details = tmdb_service.get_movie_details(tmdb_movie['id'])
                    
                    if not movie_details:
                        failed_count += 1
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
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Created: {movie.title}')
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  ↻ Updated: {movie.title}')
                        )
                
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed: {tmdb_movie.get("title", "Unknown")} - {str(e)}')
                    )
            
            # Break if trending (only 1 page available)
            if category == 'trending':
                break
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✅ Sync Complete!'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed_count}'))
        self.stdout.write('='*50)