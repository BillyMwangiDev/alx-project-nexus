from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.core.cache import cache
import hashlib

from .models import MovieMetadata, UserProfile, Rating, Playlist
from .serializers import (
    MovieMetadataSerializer, MovieMetadataListSerializer,
    UserProfileSerializer, RatingSerializer, RatingCreateSerializer,
    PlaylistSerializer, PlaylistListSerializer, UserRegistrationSerializer,
    UserSerializer
)
from .cache import cached_query, CacheManager, CacheKeys
from .filters import MovieMetadataFilter


class MovieMetadataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MovieMetadata with Redis caching
    
    List, create, retrieve, update, and delete movies
    """
    queryset = MovieMetadata.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'overview']
    ordering_fields = ['popularity', 'vote_average', 'release_date', 'created_at']
    ordering = ['-popularity']
    
    def get_serializer_class(self):
        """Use lighter serializer for list view"""
        if self.action == 'list':
            return MovieMetadataListSerializer
        return MovieMetadataSerializer
    
    def get_queryset(self):
        """Apply custom filters"""
        queryset = MovieMetadata.objects.all()
        
        # Apply custom filterset
        filterset = MovieMetadataFilter(self.request.query_params, queryset=queryset)
        return filterset.qs
    
    def list(self, request, *args, **kwargs):
        """List movies with caching"""
        # Generate cache key from query params
        query_params = str(sorted(request.GET.items()))
        cache_key_hash = hashlib.md5(query_params.encode()).hexdigest()
        cache_key = CacheKeys.movie_list(cache_key_hash)
        
        # Try cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)
        
        # Get fresh data
        response = super().list(request, *args, **kwargs)
        
        # Cache for 15 minutes
        cache.set(cache_key, response.data, timeout=60*15)
        
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single movie with caching"""
        # Cache individual movie details for 30 minutes
        movie_id = kwargs.get('pk')
        cache_key = CacheKeys.movie_detail(movie_id)
        
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)
        
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60*30)
        
        return response
    
    def create(self, request, *args, **kwargs):
        """Create movie and invalidate list cache"""
        response = super().create(request, *args, **kwargs)
        
        # Invalidate movie list cache
        CacheManager.invalidate_pattern('movie:list:*')
        
        return response
    
    def update(self, request, *args, **kwargs):
        """Update movie and invalidate its cache"""
        response = super().update(request, *args, **kwargs)
        
        # Invalidate this movie's cache
        movie_id = kwargs.get('pk')
        CacheManager.invalidate_movie(movie_id)
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Delete movie and invalidate cache"""
        movie_id = kwargs.get('pk')
        response = super().destroy(request, *args, **kwargs)
        
        # Invalidate this movie's cache
        CacheManager.invalidate_movie(movie_id)
        
        return response
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending movies with caching"""
        cache_key = CacheKeys.trending_movies()
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Get fresh data
        movies = self.queryset.order_by('-popularity')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        
        # Cache for 6 hours
        cache.set(cache_key, serializer.data, timeout=60*60*6)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently added movies"""
        # Cache for 30 minutes
        cache_key = 'movies:recent'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        movies = self.queryset.order_by('-created_at')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        
        cache.set(cache_key, serializer.data, timeout=60*30)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top rated movies with caching"""
        cache_key = CacheKeys.top_rated_movies()
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Get fresh data
        movies = self.queryset.filter(vote_count__gte=100).order_by('-vote_average')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        
        # Cache for 6 hours
        cache.set(cache_key, serializer.data, timeout=60*60*6)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def recommendations(self, request):
        """Get personalized recommendations with caching (allows anonymous users)"""
        from apps.movies_api.services.recommendation_service import recommendation_service

        user = request.user
        limit = int(request.query_params.get('limit', 20))

        # Use 'anonymous' key for unauthenticated users to match recommendation service
        user_id = user.id if getattr(user, 'is_authenticated', False) else 'anonymous'

        # Generate cache key
        cache_key = f"{CacheKeys.recommendations(user_id)}:limit:{limit}"

        # Try cache first
        cached_recommendations = cache.get(cache_key)
        if cached_recommendations is not None:
            return Response(cached_recommendations)

        # Get fresh recommendations
        recommendations = recommendation_service.get_recommendations_for_user(user, limit)
        
        # Format response
        results = []
        for rec in recommendations:
            movie_data = MovieMetadataListSerializer(rec['movie']).data
            movie_data['match_score'] = rec['match_score']
            results.append(movie_data)
        
        # Cache for 30 minutes
        cache.set(cache_key, results, timeout=60*30)
        
        return Response(results)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Get movies similar to this one with caching"""
        from apps.movies_api.services.recommendation_service import recommendation_service
        
        movie = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        
        # Cache similar movies for 1 hour
        cache_key = f'movie:similar:{movie.id}:limit:{limit}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        similar_movies = recommendation_service.get_similar_movies(movie, limit)
        serializer = MovieMetadataListSerializer(similar_movies, many=True)
        
        cache.set(cache_key, serializer.data, timeout=60*60)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def match_score(self, request, pk=None):
        """Get match score for this movie for the current user"""
        from apps.movies_api.services.recommendation_service import recommendation_service
        
        movie = self.get_object()
        
        # Cache match scores for 30 minutes
        cache_key = f'match_score:user:{request.user.id}:movie:{movie.id}'
        cached_score = cache.get(cache_key)
        if cached_score is not None:
            return Response({
                'movie_id': movie.id,
                'title': movie.title,
                'match_score': cached_score
            })
        
        score = recommendation_service.calculate_match_score(request.user, movie)
        
        cache.set(cache_key, score, timeout=60*30)
        
        return Response({
            'movie_id': movie.id,
            'title': movie.title,
            'match_score': score
        })


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile
    
    Manage user profiles
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own profile"""
        # Fix for Swagger: check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            return UserProfile.objects.none()
        
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Get or update current user's profile"""
        profile = request.user.profile
        
        if request.method == 'GET':
            # Cache user profile for 15 minutes
            cache_key = f'user:profile:{request.user.id}'
            cached_profile = cache.get(cache_key)
            if cached_profile is not None:
                return Response(cached_profile)
            
            serializer = self.get_serializer(profile)
            cache.set(cache_key, serializer.data, timeout=60*15)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(profile, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # Invalidate user's cache after update
            CacheManager.invalidate_user_cache(request.user.id)
            
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about current user's movie watching habits with caching"""
        from apps.movies_api.services.recommendation_service import recommendation_service
        
        # Cache user stats for 1 hour
        cache_key = f'user:stats:{request.user.id}'
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return Response(cached_stats)
        
        stats = recommendation_service.get_user_statistics(request.user)
        
        if not stats:
            return Response({
                'message': 'No statistics available. Start rating some movies!'
            })
        
        # Add serialized highest and lowest rated movies
        if 'highest_rated' in stats and stats['highest_rated']:
            from apps.movies_api.serializers import RatingSerializer
            stats['highest_rated'] = RatingSerializer(stats['highest_rated']).data
        
        if 'lowest_rated' in stats and stats['lowest_rated']:
            from apps.movies_api.serializers import RatingSerializer
            stats['lowest_rated'] = RatingSerializer(stats['lowest_rated']).data
        
        # Cache for 1 hour
        cache.set(cache_key, stats, timeout=60*60)
        
        return Response(stats)


class RatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Rating
    
    Create, read, update, and delete movie ratings
    """
    queryset = Rating.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['movie', 'score']
    ordering_fields = ['created_at', 'score']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializer for create"""
        if self.action == 'create':
            return RatingCreateSerializer
        return RatingSerializer
    
    def get_queryset(self):
        """Filter ratings by user if requested"""
        queryset = Rating.objects.all()
        user_id = self.request.query_params.get('user', None)
        
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the user to the current user and invalidate caches"""
        rating = serializer.save(user=self.request.user)
        
        # Invalidate relevant caches
        CacheManager.invalidate_user_cache(self.request.user.id)
        CacheManager.invalidate_movie(rating.movie.id)
    
    def update(self, request, *args, **kwargs):
        """Only allow users to update their own ratings"""
        rating = self.get_object()
        if rating.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only update your own ratings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = super().update(request, *args, **kwargs)
        
        # Invalidate caches
        CacheManager.invalidate_user_cache(request.user.id)
        CacheManager.invalidate_movie(rating.movie.id)
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Only allow users to delete their own ratings"""
        rating = self.get_object()
        if rating.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only delete your own ratings."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        movie_id = rating.movie.id
        user_id = request.user.id
        
        response = super().destroy(request, *args, **kwargs)
        
        # Invalidate caches
        CacheManager.invalidate_user_cache(user_id)
        CacheManager.invalidate_movie(movie_id)
        
        return response
    
    @action(detail=False, methods=['get'])
    def my_ratings(self, request):
        """Get current user's ratings with caching"""
        # Cache user ratings for 15 minutes
        cache_key = CacheKeys.user_ratings(request.user.id)
        cached_ratings = cache.get(cache_key)
        if cached_ratings is not None:
            return Response(cached_ratings)
        
        ratings = Rating.objects.filter(user=request.user)
        serializer = self.get_serializer(ratings, many=True)
        
        cache.set(cache_key, serializer.data, timeout=60*15)
        return Response(serializer.data)


class PlaylistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Playlist
    
    Create, read, update, and delete playlists
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['visibility', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use lighter serializer for list view"""
        if self.action == 'list':
            return PlaylistListSerializer
        return PlaylistSerializer
    
    def get_queryset(self):
        """
        Return public playlists and user's own playlists
        """
        if self.request.user.is_authenticated:
            return Playlist.objects.filter(
                visibility='public'
            ) | Playlist.objects.filter(owner=self.request.user)
        return Playlist.objects.filter(visibility='public')
    
    def perform_create(self, serializer):
        """Set the owner to the current user and invalidate cache"""
        playlist = serializer.save(owner=self.request.user)
        
        # Invalidate user's playlist cache
        cache.delete(f'playlists:user:{self.request.user.id}')
    
    def update(self, request, *args, **kwargs):
        """Only allow owners to update their playlists"""
        playlist = self.get_object()
        if playlist.owner != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only update your own playlists."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response = super().update(request, *args, **kwargs)
        
        # Invalidate playlist cache
        cache.delete(f'playlist:{playlist.id}')
        cache.delete(f'playlists:user:{request.user.id}')
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Only allow owners to delete their playlists"""
        playlist = self.get_object()
        if playlist.owner != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only delete your own playlists."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.user.id
        response = super().destroy(request, *args, **kwargs)
        
        # Invalidate caches
        cache.delete(f'playlists:user:{user_id}')
        
        return response
    
    @action(detail=False, methods=['get'])
    def my_playlists(self, request):
        """Get current user's playlists with caching"""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Cache user's playlists for 15 minutes
        cache_key = f'playlists:user:{request.user.id}'
        cached_playlists = cache.get(cache_key)
        if cached_playlists is not None:
            return Response(cached_playlists)
        
        playlists = Playlist.objects.filter(owner=request.user)
        serializer = self.get_serializer(playlists, many=True)
        
        cache.set(cache_key, serializer.data, timeout=60*15)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_movie(self, request, pk=None):
        """Add a movie to the playlist"""
        playlist = self.get_object()
        
        if playlist.owner != request.user:
            return Response(
                {"detail": "You can only modify your own playlists."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response(
                {"detail": "movie_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            movie = MovieMetadata.objects.get(id=movie_id)
            playlist.movies.add(movie)
            
            # Invalidate playlist cache
            cache.delete(f'playlist:{playlist.id}')
            cache.delete(f'playlists:user:{request.user.id}')
            
            return Response({"detail": "Movie added to playlist."})
        except MovieMetadata.DoesNotExist:
            return Response(
                {"detail": "Movie not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_movie(self, request, pk=None):
        """Remove a movie from the playlist"""
        playlist = self.get_object()
        
        if playlist.owner != request.user:
            return Response(
                {"detail": "You can only modify your own playlists."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response(
                {"detail": "movie_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            movie = MovieMetadata.objects.get(id=movie_id)
            playlist.movies.remove(movie)
            
            # Invalidate playlist cache
            cache.delete(f'playlist:{playlist.id}')
            cache.delete(f'playlists:user:{request.user.id}')
            
            return Response({"detail": "Movie removed from playlist."})
        except MovieMetadata.DoesNotExist:
            return Response(
                {"detail": "Movie not found."},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully",
                "user": UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def tmdb_search(request):
    """
    Search movies on TMDb API with caching
    """
    from apps.movies_api.services.tmdb_service import tmdb_service
    
    query = request.query_params.get('q', '')
    
    if not query:
        return Response(
            {"error": "Query parameter 'q' is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Cache TMDb search results for 1 hour
    cache_key = f'tmdb:search:{query.lower()}'
    cached_results = cache.get(cache_key)
    if cached_results is not None:
        return Response(cached_results)
    
    results = tmdb_service.search_movies(query)
    
    if not results:
        return Response(
            {"error": "TMDb API request failed"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Cache the results
    cache.set(cache_key, results, timeout=60*60)
    
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_movie_from_tmdb(request):
    """
    Import a movie from TMDb to local database
    """
    from apps.movies_api.services.tmdb_service import tmdb_service
    
    tmdb_id = request.data.get('tmdb_id')
    
    if not tmdb_id:
        return Response(
            {"error": "tmdb_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check if already exists
        existing_movie = MovieMetadata.objects.filter(tmdb_id=tmdb_id).first()
        if existing_movie:
            return Response(
                {
                    "message": "Movie already exists in database",
                    "movie": MovieMetadataSerializer(existing_movie).data
                },
                status=status.HTTP_200_OK
            )
        
        # Fetch from TMDb
        movie_details = tmdb_service.get_movie_details(tmdb_id)
        
        if not movie_details:
            return Response(
                {"error": "Movie not found on TMDb"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Normalize and save
        movie_data = tmdb_service.normalize_movie_data(movie_details)
        movie = MovieMetadata.objects.create(**movie_data)
        
        # Invalidate movie list cache
        CacheManager.invalidate_pattern('movie:list:*')
        
        return Response(
            {
                "message": "Movie imported successfully",
                "movie": MovieMetadataSerializer(movie).data
            },
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )