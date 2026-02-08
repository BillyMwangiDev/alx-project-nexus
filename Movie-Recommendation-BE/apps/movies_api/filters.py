import django_filters
from .models import MovieMetadata
from django.db import connection

class MovieMetadataFilter(django_filters.FilterSet):
    """
    Custom optimized filters for MovieMetadata.
    Includes normalized genre filtering to maintain DB consistency.
    """
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
    
    # Genre filtering
    genre = django_filters.CharFilter(method='filter_by_genre')
    
    class Meta:
        model = MovieMetadata
        fields = [
            'title', 'year', 'year_gte', 'year_lte', 'min_rating', 
            'max_rating', 'min_popularity', 'min_runtime', 'max_runtime', 'genre'
        ]
    
    def filter_by_genre(self, queryset, name, value):
        """
        Optimized genre filtering with cross-DB semantic consistency.
        Normalizes the search term to lowercase to match canonical stored data.
        """
        if not value:
            return queryset

        # Normalize the search value to lowercase to match stored canonical format
        value_lower = value.lower()
        
        if connection.vendor == 'postgresql':
            # PostgreSQL: Use native JSONB containment ([item] in list)
            # This avoids substring matches (e.g., 'Drama' won't match 'Melodrama')
            return queryset.filter(genres__contains=[value_lower])
        
        # SQLite/Other: Use DB-level string search
        # Note: Since we store genres as lowercase, icontains acts as a safe fallback
        return queryset.filter(genres__icontains=value_lower)