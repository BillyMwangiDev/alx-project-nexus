from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User

from .models import MovieMetadata, UserProfile, Rating, Playlist
from .serializers import (
    MovieMetadataSerializer, MovieMetadataListSerializer,
    UserProfileSerializer, RatingSerializer, RatingCreateSerializer,
    PlaylistSerializer, PlaylistListSerializer, UserRegistrationSerializer,
    UserSerializer
)


class MovieMetadataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MovieMetadata
    
    List, create, retrieve, update, and delete movies
    """
    queryset = MovieMetadata.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['release_date']  # Removed 'genres' since it's a JSONField
    search_fields = ['title', 'overview']
    ordering_fields = ['popularity', 'vote_average', 'release_date', 'created_at']
    ordering = ['-popularity']
    
    def get_serializer_class(self):
        """Use lighter serializer for list view"""
        if self.action == 'list':
            return MovieMetadataListSerializer
        return MovieMetadataSerializer
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending movies"""
        movies = self.queryset.order_by('-popularity')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently added movies"""
        movies = self.queryset.order_by('-created_at')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top rated movies"""
        movies = self.queryset.filter(vote_count__gte=100).order_by('-vote_average')[:20]
        serializer = MovieMetadataListSerializer(movies, many=True)
        return Response(serializer.data)


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
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(profile, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


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
        """Set the user to the current user"""
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only allow users to update their own ratings"""
        rating = self.get_object()
        if rating.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only update your own ratings."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow users to delete their own ratings"""
        rating = self.get_object()
        if rating.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only delete your own ratings."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_ratings(self, request):
        """Get current user's ratings"""
        ratings = Rating.objects.filter(user=request.user)
        serializer = self.get_serializer(ratings, many=True)
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
        """Set the owner to the current user"""
        serializer.save(owner=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only allow owners to update their playlists"""
        playlist = self.get_object()
        if playlist.owner != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only update your own playlists."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow owners to delete their playlists"""
        playlist = self.get_object()
        if playlist.owner != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You can only delete your own playlists."},
                status=status.HTTP_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_playlists(self, request):
        """Get current user's playlists"""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        playlists = Playlist.objects.filter(owner=request.user)
        serializer = self.get_serializer(playlists, many=True)
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