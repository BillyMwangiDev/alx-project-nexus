from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.core.cache import cache
import hashlib
import logging

from .models import MovieMetadata, UserProfile, Rating, Playlist
from .serializers import (
    MovieMetadataSerializer, MovieMetadataListSerializer,
    UserProfileSerializer, RatingSerializer, RatingCreateSerializer,
    PlaylistSerializer, PlaylistListSerializer, UserRegistrationSerializer,
    UserSerializer
)
from .cache import cached_query, CacheManager, CacheKeys
from .filters import MovieMetadataFilter

# Configure logger for this module
logger = logging.getLogger(__name__)

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
        """Apply custom filters with field optimization"""
        # Note: We use self.get_queryset() internally to benefit from .only()
        queryset = MovieMetadata.objects.all()
        
        # FIX: poster_url is a @property (Python-level), not a DB column.
        # We must request 'poster_path' so the DB can fetch the actual field.
        if self.action == 'list':
            queryset = queryset.only(
                'id', 'tmdb_id', 'title', 'release_date', 
                'poster_path', 'vote_average', 'popularity', 'genres'
            )
        
        # Apply custom filterset
        filterset = MovieMetadataFilter(self.request.query_params, queryset=queryset)
        return filterset.qs
    
    def list(self, request, *args, **kwargs):
        """List movies with caching"""
        # FIX: Use urlencode() to prevent dropping duplicate keys and ensure consistency.
        # usedforsecurity=False silences security lints for non-cryptographic MD5 use.
        query_params_string = request.GET.urlencode()
        cache_key_hash = hashlib.md5(
            query_params_string.encode(), 
            usedforsecurity=False
        ).hexdigest()
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
        CacheManager.invalidate_pattern('movie:list:*')
        return response
    
    def update(self, request, *args, **kwargs):
        """Update movie and invalidate its cache"""
        response = super().update(request, *args, **kwargs)
        movie_id = kwargs.get('pk')
        CacheManager.invalidate_movie(movie_id)
        return response
    
    def destroy(self, request, *args, **kwargs):
        """Delete movie and invalidate cache"""
        movie_id = kwargs.get('pk')
        response = super().destroy(request, *args, **kwargs)
        CacheManager.invalidate_movie(movie_id)
        return response
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending movies with caching"""
        cache_key = CacheKeys.trending_movies()
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        # Use get_queryset() to ensure field optimization is applied
        movies = self.get_queryset().order_by('-popularity')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        
        cache.set(cache_key, serializer.data, timeout=60*60*6)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently added movies"""
        cache_key = 'movies:recent'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        movies = self.get_queryset().order_by('-created_at')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        
        cache.set(cache_key, serializer.data, timeout=60*30)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top rated movies with caching"""
        cache_key = CacheKeys.top_rated_movies()
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        movies = self.get_queryset().filter(vote_count__gte=100).order_by('-vote_average')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        
        cache.set(cache_key, serializer.data, timeout=60*60*6)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def recommendations(self, request):
        """Get personalized recommendations with caching"""
        from apps.movies_api.services.recommendation_service import recommendation_service

        user = request.user
        limit = int(request.query_params.get('limit', 20))
        user_id = user.id if getattr(user, 'is_authenticated', False) else 'anonymous'

        cache_key = f"{CacheKeys.recommendations(user_id)}:limit:{limit}"
        cached_recommendations = cache.get(cache_key)
        if cached_recommendations is not None:
            return Response(cached_recommendations)

        recommendations = recommendation_service.get_recommendations_for_user(user, limit)
        
        results = []
        for rec in recommendations:
            movie_data = MovieMetadataListSerializer(rec['movie']).data
            movie_data['match_score'] = rec['match_score']
            results.append(movie_data)
        
        cache.set(cache_key, results, timeout=60*30)
        return Response(results)
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Get movies similar to this one with caching"""
        from apps.movies_api.services.recommendation_service import recommendation_service
        
        movie = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        
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
    """ViewSet for UserProfile management"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserProfile.objects.none()
        
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        profile = request.user.profile
        
        if request.method == 'GET':
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
            CacheManager.invalidate_user_cache(request.user.id)
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        from apps.movies_api.services.recommendation_service import recommendation_service
        
        cache_key = f'user:stats:{request.user.id}'
        cached_stats = cache.get(cache_key)
        if cached_stats is not None:
            return Response(cached_stats)
        
        stats = recommendation_service.get_user_statistics(request.user)
        if not stats:
            return Response({'message': 'No statistics available. Start rating some movies!'})
        
        # Serialize highlight objects if they exist
        for key in ['highest_rated', 'lowest_rated']:
            if stats.get(key):
                stats[key] = RatingSerializer(stats[key]).data
        
        cache.set(cache_key, stats, timeout=60*60)
        return Response(stats)


class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet for movie ratings"""
    queryset = Rating.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['movie', 'score']
    ordering_fields = ['created_at', 'score']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RatingCreateSerializer
        return RatingSerializer
    
    def get_queryset(self):
        queryset = Rating.objects.all()
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        return queryset
    
    def perform_create(self, serializer):
        rating = serializer.save(user=self.request.user)
        CacheManager.invalidate_user_cache(self.request.user.id)
        CacheManager.invalidate_movie(rating.movie.id)
    
    def update(self, request, *args, **kwargs):
        rating = self.get_object()
        if rating.user != request.user and not request.user.is_staff:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
        response = super().update(request, *args, **kwargs)
        CacheManager.invalidate_user_cache(request.user.id)
        CacheManager.invalidate_movie(rating.movie.id)
        return response
    
    def destroy(self, request, *args, **kwargs):
        rating = self.get_object()
        if rating.user != request.user and not request.user.is_staff:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        
        movie_id, user_id = rating.movie.id, request.user.id
        response = super().destroy(request, *args, **kwargs)
        CacheManager.invalidate_user_cache(user_id)
        CacheManager.invalidate_movie(movie_id)
        return response


class PlaylistViewSet(viewsets.ModelViewSet):
    """ViewSet for playlists"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['visibility', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        return PlaylistListSerializer if self.action == 'list' else PlaylistSerializer
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Playlist.objects.filter(visibility='public') | Playlist.objects.filter(owner=self.request.user)
        return Playlist.objects.filter(visibility='public')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        cache.delete(f'playlists:user:{self.request.user.id}')


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            "message": "User registered successfully",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def tmdb_search(request):
    from apps.movies_api.services.tmdb_service import tmdb_service
    query = request.query_params.get('q', '')
    if not query:
        return Response({"error": "Query required"}, status=status.HTTP_400_BAD_REQUEST)
    
    cache_key = f'tmdb:search:{query.lower()}'
    cached_results = cache.get(cache_key)
    if cached_results: return Response(cached_results)
    
    results = tmdb_service.search_movies(query)
    if not results:
        return Response({"error": "TMDb API error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    cache.set(cache_key, results, timeout=60*60)
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_movie_from_tmdb(request):
    from apps.movies_api.services.tmdb_service import tmdb_service
    tmdb_id = request.data.get('tmdb_id')
    if not tmdb_id:
        return Response({"error": "tmdb_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        existing_movie = MovieMetadata.objects.filter(tmdb_id=tmdb_id).first()
        if existing_movie:
            return Response({
                "message": "Movie already exists",
                "movie": MovieMetadataSerializer(existing_movie).data
            }, status=status.HTTP_200_OK)
        
        movie_details = tmdb_service.get_movie_details(tmdb_id)
        if not movie_details:
            return Response({"error": "Not found on TMDb"}, status=status.HTTP_404_NOT_FOUND)
        
        movie_data = tmdb_service.normalize_movie_data(movie_details)
        movie = MovieMetadata.objects.create(**movie_data)
        CacheManager.invalidate_pattern('movie:list:*')
        
        return Response({
            "message": "Imported successfully",
            "movie": MovieMetadataSerializer(movie).data
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        # FIX: Avoid leaking str(e) to client. Log detailed error internally.
        logger.exception("TMDb import failed for tmdb_id=%s", tmdb_id)
        return Response(
            {"error": "An internal error occurred during import."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )