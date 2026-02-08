from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    MovieMetadataViewSet,
    UserProfileViewSet,
    RatingViewSet,
    PlaylistViewSet,
    register_user,
    tmdb_search,          
    import_movie_from_tmdb 
)

router = DefaultRouter()
router.register(r'movies', MovieMetadataViewSet, basename='movie')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'playlists', PlaylistViewSet, basename='playlist')

urlpatterns = [
    # Authentication
    path('auth/register/', register_user, name='register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # TMDb Integration Endpoints
    path('tmdb/search/', tmdb_search, name='tmdb_search'),
    path('tmdb/import/', import_movie_from_tmdb, name='tmdb_import'),
    
    # API endpoints
    path('', include(router.urls)),
]