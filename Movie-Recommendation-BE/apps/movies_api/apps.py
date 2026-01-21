from django.apps import AppConfig



class MoviesApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.movies_api'  
    verbose_name = 'Movies API'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.movies_api.signals