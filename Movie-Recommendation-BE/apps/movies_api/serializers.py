from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MovieMetadata, UserProfile, Rating, Playlist


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'favorite_genres', 'bio', 'avatar_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'email', 'created_at', 'updated_at']


class MovieMetadataSerializer(serializers.ModelSerializer):
    """Serializer for MovieMetadata model"""
    poster_url = serializers.ReadOnlyField()
    release_year = serializers.SerializerMethodField()
    
    class Meta:
        model = MovieMetadata
        fields = [
            'id', 'tmdb_id', 'title', 'overview', 'release_date', 'release_year',
            'poster_path', 'poster_url', 'backdrop_path', 'vote_average', 
            'vote_count', 'popularity', 'genres', 'runtime', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_release_year(self, obj):
        """Extract year from release_date"""
        if obj.release_date:
            return obj.release_date.year
        return None


class MovieMetadataListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    poster_url = serializers.ReadOnlyField()
    release_year = serializers.SerializerMethodField()
    
    class Meta:
        model = MovieMetadata
        fields = ['id', 'tmdb_id', 'title', 'release_date', 'release_year', 
                  'poster_url', 'vote_average', 'popularity', 'genres']
    
    def get_release_year(self, obj):
        if obj.release_date:
            return obj.release_date.year
        return None


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for Rating model"""
    username = serializers.CharField(source='user.username', read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=MovieMetadata.objects.all(),
        source='movie',
        write_only=True
    )
    
    class Meta:
        model = Rating
        fields = ['id', 'username', 'movie_title', 'movie_id', 'score', 'review', 'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'movie_title', 'created_at', 'updated_at']
    
    def validate_score(self, value):
        """Ensure score is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Score must be between 1 and 5")
        return value


class RatingCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating ratings"""
    class Meta:
        model = Rating
        fields = ['movie', 'score', 'review']


class RatingDetailSerializer(serializers.ModelSerializer):
    """Detailed rating serializer with nested movie data"""
    user = UserSerializer(read_only=True)
    movie = MovieMetadataListSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'user', 'movie', 'score', 'review', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for Playlist model"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    movies = MovieMetadataListSerializer(many=True, read_only=True)
    movie_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MovieMetadata.objects.all(),
        source='movies',
        write_only=True,
        required=False
    )
    movie_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Playlist
        fields = [
            'id', 'owner_username', 'name', 'description', 'visibility', 
            'movies', 'movie_ids', 'movie_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner_username', 'created_at', 'updated_at']


class PlaylistListSerializer(serializers.ModelSerializer):
    """Lighter serializer for playlist lists"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    movie_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Playlist
        fields = ['id', 'owner_username', 'name', 'description', 'visibility', 'movie_count', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        """Check that passwords match"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
      