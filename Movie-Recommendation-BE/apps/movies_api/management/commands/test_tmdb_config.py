from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test TMDb API configuration'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write('Testing TMDb API Configuration')
        self.stdout.write('='*60)
        
        # Check if API key is configured
        api_key = getattr(settings, 'TMDB_API_KEY', None)
        
        if not api_key:
            self.stdout.write(self.style.ERROR('❌ TMDB_API_KEY is not configured'))
            self.stdout.write('\nPlease add your TMDb API key to settings.py:')
            self.stdout.write('  TMDB_API_KEY = "your_api_key_here"')
            return
        
        if api_key == 'your_tmdb_api_key_here' or api_key == '' or api_key == 'your_actual_api_key_here':
            self.stdout.write(self.style.ERROR('❌ TMDB_API_KEY is set to default/empty value'))
            self.stdout.write('\nPlease replace with your actual TMDb API key:')
            self.stdout.write('  1. Go to https://www.themoviedb.org/settings/api')
            self.stdout.write('  2. Copy your API Key (v3 auth)')
            self.stdout.write('  3. Add it to config/settings.py')
            return
        
        # Mask the API key for display
        masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
        self.stdout.write(self.style.SUCCESS(f'✓ TMDB_API_KEY is configured: {masked_key}'))
        
        # Try to make a test request
        self.stdout.write('\nTesting API connection...')
        
        try:
            from apps.movies_api.services.tmdb_service import tmdb_service
            
            # Try to get popular movies
            response = tmdb_service.get_popular_movies(page=1)
            
            if response and 'results' in response:
                movies = response['results'][:3]
                
                self.stdout.write(self.style.SUCCESS('✓ Successfully connected to TMDb API!'))
                self.stdout.write(f'\nFetched {len(response["results"])} popular movies')
                self.stdout.write('\nSample movies:')
                
                for idx, movie in enumerate(movies, 1):
                    title = movie.get('title', 'Unknown')
                    year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A'
                    rating = movie.get('vote_average', 0)
                    self.stdout.write(f'  {idx}. {title} ({year}) - ⭐ {rating}/10')
                
                self.stdout.write(self.style.SUCCESS('\n✅ TMDb integration is working correctly!'))
                self.stdout.write('\nYou can now run:')
                self.stdout.write('  python manage.py sync_tmdb_movies --category popular --pages 5')
                self.stdout.write('  python manage.py search_tmdb "Inception"')
                
            else:
                self.stdout.write(self.style.ERROR('❌ API returned unexpected response'))
                
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'❌ Configuration Error: {str(e)}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Connection Error: {str(e)}'))
            self.stdout.write('\nPossible issues:')
            self.stdout.write('  1. Invalid API key')
            self.stdout.write('  2. Network connection problem')
            self.stdout.write('  3. TMDb API is down')
            self.stdout.write('\nVerify your API key at: https://www.themoviedb.org/settings/api')
        
        self.stdout.write('\n' + '='*60)