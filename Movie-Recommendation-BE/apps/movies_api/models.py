from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class MovieMetadata(models.Model):
    """
    Stores cached movie data from TMDb to reduce external API calls
    and enable fast relational queries.
    """
    tmdb_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    backdrop_path = models.CharField(max_length=255, blank=True)
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0.0)
    genres = models.JSONField(default=list)  # Store as list of lowercase genre names
    runtime = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-popularity']
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'
        indexes = [
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['-popularity']),
            models.Index(fields=['release_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.release_date.year if self.release_date else 'N/A'})"

    def save(self, *args, **kwargs):
        """Normalize genres to lowercase before saving for consistent filtering."""
        if isinstance(self.genres, list):
            self.genres = [g.lower() for g in self.genres if isinstance(g, str)]
        super().save(*args, **kwargs)
    
    @property
    def poster_url(self):
        """Generate full TMDb poster URL"""
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None


class UserProfile(models.Model):
    """
    Extended user profile for personalization features.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    favorite_genres = models.JSONField(default=list)  # List of favorite genre names
    bio = models.TextField(max_length=500, blank=True)
    avatar_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        """Normalize favorite genres to lowercase for consistent recommendation matching."""
        if isinstance(self.favorite_genres, list):
            self.favorite_genres = [g.lower() for g in self.favorite_genres if isinstance(g, str)]
        super().save(*args, **kwargs)


class Rating(models.Model):
    """
    User ratings for movies (1-5 stars).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(MovieMetadata, on_delete=models.CASCADE, related_name='user_ratings')
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    review = models.TextField(blank=True, max_length=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        indexes = [
            models.Index(fields=['user', 'movie']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.score}/5"


class Playlist(models.Model):
    """
    User-created collections of movies.
    """
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=500)
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='private'
    )
    movies = models.ManyToManyField(MovieMetadata, related_name='playlists', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Playlist'
        verbose_name_plural = 'Playlists'
        indexes = [
            models.Index(fields=['owner', 'visibility']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.owner.username}"
    
    @property
    def movie_count(self):
        return self.movies.count()
    
    def is_accessible_by(self, user):
        return self.visibility == 'public' or self.owner == user