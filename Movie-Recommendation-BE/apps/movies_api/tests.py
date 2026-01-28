from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from apps.movies_api.models import MovieMetadata, UserProfile, Rating, Playlist


class MovieMetadataTestCase(TestCase):
    """Test MovieMetadata model"""
    
    def setUp(self):
        self.movie = MovieMetadata.objects.create(
            tmdb_id=550,
            title="Fight Club",
            overview="A ticking-time-bomb insomniac...",
            release_date=date(1999, 10, 15),
            vote_average=8.4,
            popularity=95.3,
            genres=["Drama", "Thriller"],
            runtime=139
        )
    
    def test_movie_creation(self):
        """Test that movie is created correctly"""
        self.assertEqual(self.movie.title, "Fight Club")
        self.assertEqual(self.movie.tmdb_id, 550)
        self.assertIn("Drama", self.movie.genres)
    
    def test_movie_str(self):
        """Test movie string representation"""
        self.assertEqual(str(self.movie), "Fight Club (1999)")
    
    def test_poster_url_property(self):
        """Test poster URL generation"""
        self.movie.poster_path = "/test.jpg"
        self.assertEqual(
            self.movie.poster_url,
            "https://image.tmdb.org/t/p/w500/test.jpg"
        )


class UserProfileTestCase(TestCase):
    """Test UserProfile model and signals"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
    
    def test_profile_auto_created(self):
        """Test that profile is automatically created with user"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
    
    def test_profile_update(self):
        """Test updating user profile"""
        profile = self.user.profile
        profile.favorite_genres = ["Action", "Sci-Fi"]
        profile.bio = "Movie lover"
        profile.save()
        
        profile.refresh_from_db()
        self.assertEqual(len(profile.favorite_genres), 2)
        self.assertIn("Action", profile.favorite_genres)


class RatingTestCase(TestCase):
    """Test Rating model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.movie = MovieMetadata.objects.create(
            tmdb_id=550,
            title="Fight Club",
            vote_average=8.4
        )
    
    def test_rating_creation(self):
        """Test creating a rating"""
        rating = Rating.objects.create(
            user=self.user,
            movie=self.movie,
            score=5,
            review="Amazing movie!"
        )
        
        self.assertEqual(rating.score, 5)
        self.assertEqual(rating.user, self.user)
        self.assertEqual(rating.movie, self.movie)
    
    def test_unique_rating_constraint(self):
        """Test that user can only rate a movie once"""
        Rating.objects.create(
            user=self.user,
            movie=self.movie,
            score=5
        )
        
        # Try to create duplicate rating should raise error
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Rating.objects.create(
                user=self.user,
                movie=self.movie,
                score=4
            )


class PlaylistTestCase(TestCase):
    """Test Playlist model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.movie1 = MovieMetadata.objects.create(
            tmdb_id=550,
            title="Fight Club"
        )
        self.movie2 = MovieMetadata.objects.create(
            tmdb_id=551,
            title="The Matrix"
        )
    
    def test_playlist_creation(self):
        """Test creating a playlist"""
        playlist = Playlist.objects.create(
            owner=self.user,
            name="My Favorites",
            visibility="public"
        )
        
        self.assertEqual(playlist.name, "My Favorites")
        self.assertEqual(playlist.owner, self.user)
    
    def test_add_movies_to_playlist(self):
        """Test adding movies to playlist"""
        playlist = Playlist.objects.create(
            owner=self.user,
            name="Action Movies"
        )
        
        playlist.movies.add(self.movie1, self.movie2)
        
        self.assertEqual(playlist.movies.count(), 2)
        self.assertEqual(playlist.movie_count, 2)
    
    def test_playlist_accessibility(self):
        """Test playlist access permissions"""
        public_playlist = Playlist.objects.create(
            owner=self.user,
            name="Public List",
            visibility="public"
        )
        
        private_playlist = Playlist.objects.create(
            owner=self.user,
            name="Private List",
            visibility="private"
        )
        
        other_user = User.objects.create_user(
            username="otheruser",
            password="pass123"
        )
        
        self.assertTrue(public_playlist.is_accessible_by(other_user))
        self.assertFalse(private_playlist.is_accessible_by(other_user))
        self.assertTrue(private_playlist.is_accessible_by(self.user))


class APIEndpointTestCase(TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.movie = MovieMetadata.objects.create(
            tmdb_id=550,
            title="Fight Club",
            vote_average=8.4,
            popularity=95.3
        )
    
    def test_movie_list_endpoint(self):
        """Test GET /api/movies/"""
        response = self.client.get('/api/movies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_movie_detail_endpoint(self):
        """Test GET /api/movies/{id}/"""
        response = self.client.get(f'/api/movies/{self.movie.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Fight Club")
    
    def test_trending_endpoint(self):
        """Test GET /api/movies/trending/"""
        response = self.client.get('/api/movies/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_authentication_required_for_rating(self):
        """Test that authentication is required to create rating"""
        response = self.client.post('/api/ratings/', {
            'movie': self.movie.id,
            'score': 5
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_rating_authenticated(self):
        """Test creating rating when authenticated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/ratings/', {
            'movie': self.movie.id,
            'score': 5,
            'review': "Great movie!"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
    
    def test_get_recommendations_authenticated(self):
        """Test recommendations endpoint requires auth"""
        response = self.client.get('/api/movies/recommendations/')
        # Should work but return generic recommendations for anonymous users
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RecommendationTestCase(TestCase):
    """Test recommendation service"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        # Update user profile with favorite genres
        profile = self.user.profile
        profile.favorite_genres = ["Action", "Sci-Fi"]
        profile.save()
        
        # Create movies
        self.action_movie = MovieMetadata.objects.create(
            tmdb_id=550,
            title="Action Movie",
            genres=["Action", "Thriller"],
            vote_average=8.0,
            popularity=90.0
        )
        
        self.scifi_movie = MovieMetadata.objects.create(
            tmdb_id=551,
            title="Sci-Fi Movie",
            genres=["Sci-Fi", "Adventure"],
            vote_average=7.5,
            popularity=85.0
        )
    
    def test_match_score_calculation(self):
        """Test that match scores are calculated"""
        from apps.movies_api.services.recommendation_service import recommendation_service
        
        score = recommendation_service.calculate_match_score(self.user, self.action_movie)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_recommendations_for_user(self):
        """Test getting recommendations"""
        from apps.movies_api.services.recommendation_service import recommendation_service
        
        recommendations = recommendation_service.get_recommendations_for_user(self.user, limit=10)
        self.assertIsInstance(recommendations, list)
        
        if recommendations:
            self.assertIn('movie', recommendations[0])
            self.assertIn('match_score', recommendations[0])
            