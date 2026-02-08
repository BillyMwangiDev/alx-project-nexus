from django.apps import AppConfig


class MoviesApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.movies_api'  
    verbose_name = 'Movies API'
    
    def ready(self):
        """
        Import signals when the app is ready.
        This registration is required for the pre_save (genre normalization)
        and post_save (profile creation) logic to function automatically.
        """
        import apps.movies_api.signals