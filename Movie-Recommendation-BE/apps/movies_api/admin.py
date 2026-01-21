from django.contrib import admin

# Register your models here.
from .models import MovieMetadata, UserProfile, Rating, Playlist


@admin.register(MovieMetadata)
class MovieMetadataAdmin(admin.ModelAdmin):
    list_display = ('title', 'tmdb_id', 'release_date', 'vote_average', 'popularity', 'created_at')
    list_filter = ('release_date', 'created_at')
    search_fields = ('title', 'tmdb_id', 'overview')
    readonly_fields = ('created_at', 'updated_at', 'poster_url')
    ordering = ('-popularity',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tmdb_id', 'title', 'overview', 'release_date', 'runtime')
        }),
        ('Media', {
            'fields': ('poster_path', 'poster_url', 'backdrop_path')
        }),
        ('Ratings & Popularity', {
            'fields': ('vote_average', 'vote_count', 'popularity')
        }),
        ('Categories', {
            'fields': ('genres',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_favorite_genres', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Preferences', {
            'fields': ('favorite_genres', 'bio', 'avatar_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_favorite_genres(self, obj):
        return ', '.join(obj.favorite_genres) if obj.favorite_genres else 'None'
    get_favorite_genres.short_description = 'Favorite Genres'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('user__username', 'movie__title', 'review')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Rating Info', {
            'fields': ('user', 'movie', 'score')
        }),
        ('Review', {
            'fields': ('review',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'visibility', 'get_movie_count', 'created_at')
    list_filter = ('visibility', 'created_at')
    search_fields = ('name', 'owner__username', 'description')
    readonly_fields = ('created_at', 'updated_at', 'get_movie_count')
    filter_horizontal = ('movies',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Playlist Info', {
            'fields': ('owner', 'name', 'description', 'visibility')
        }),
        ('Movies', {
            'fields': ('movies', 'get_movie_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_movie_count(self, obj):
        return obj.movie_count
    get_movie_count.short_description = 'Number of Movies'