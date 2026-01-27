import django_filters
from .models import MovieMetadata


class MovieMetadataFilter(django_filters.FilterSet):
    """
    Custom filters for MovieMetadata
    """
    # Title search (case-insensitive, partial match)
    title = django_filters.CharFilter(lookup_expr='icontains')
    
    # Year filtering
    year = django_filters.NumberFilter(field_name='release_date', lookup_expr='year')
    year_gte = django_filters.NumberFilter(field_name='release_date', lookup_expr='year__gte')
    year_lte = django_filters.NumberFilter(field_name='release_date', lookup_expr='year__lte')
    
    # Rating filtering
    min_rating = django_filters.NumberFilter(field_name='vote_average', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='vote_average', lookup_expr='lte')
    
    # Popularity filtering
    min_popularity = django_filters.NumberFilter(field_name='popularity', lookup_expr='gte')
    
    # Runtime filtering
    min_runtime = django_filters.NumberFilter(field_name='runtime', lookup_expr='gte')
    max_runtime = django_filters.NumberFilter(field_name='runtime', lookup_expr='lte')
    
    # Genre filtering (contains)
    genre = django_filters.CharFilter(method='filter_by_genre')
    
    class Meta:
        model = MovieMetadata
        fields = ['title', 'year', 'year_gte', 'year_lte', 'min_rating', 'max_rating', 
                  'min_popularity', 'min_runtime', 'max_runtime', 'genre']
    
    def filter_by_genre(self, queryset, name, value):
        """
        Filter movies that contain the specified genre in their genres JSON field
        Works with both SQLite and PostgreSQL
        """
        # For SQLite: use Python filtering
        # For PostgreSQL: use native JSON contains
        from django.db import connection
        
        if connection.vendor == 'sqlite':
            # SQLite: Filter in Python (less efficient but works)
            movie_ids = []
            for movie in queryset:
                if movie.genres and value in movie.genres:
                    movie_ids.append(movie.id)
            return queryset.filter(id__in=movie_ids)
        else:
            # PostgreSQL: Use native JSON contains
            return queryset.filter(genres__contains=[value])