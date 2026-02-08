from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    MovieMetadataViewSet,
    UserProfileViewSet,
    RatingViewSet,
    PlaylistViewSet,
    register_user
)

# Create router and register viewsets
# This automatically generates the list and detail routes for each resource.
router = DefaultRouter()
router.register(r'movies', MovieMetadataViewSet, basename='movie')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'playlists', PlaylistViewSet, basename='playlist')

urlpatterns = [
    # Authentication endpoints
    # Provides user registration and JWT token management (Login/Refresh)
    path('auth/register/', register_user, name='register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    # Includes all routes registered with the router (e.g., /api/movies/, /api/profiles/)
    path('', include(router.urls)),
]