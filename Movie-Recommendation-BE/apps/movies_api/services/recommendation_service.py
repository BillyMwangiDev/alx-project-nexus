from django.db.models import Avg, Count, Q
from apps.movies_api.models import MovieMetadata, Rating, UserProfile
from typing import List, Dict


class RecommendationService:
    """
    Service for generating personalized movie recommendations
    """
    
    @staticmethod
    def calculate_match_score(user, movie: MovieMetadata) -> float:
        """
        Calculate how well a movie matches a user's preferences
        
        Score is based on:
        - User's favorite genres (40%)
        - User's rating history (30%)
        - Movie's overall rating (20%)
        - Movie's popularity (10%)
        
        Returns: Score from 0-100
        """
        if not user.is_authenticated:
            # For anonymous users, use basic scoring
            return RecommendationService._anonymous_score(movie)
        
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return RecommendationService._anonymous_score(movie)
        
        score = 0.0
        
        # 1. Genre Match (40 points)
        favorite_genres = profile.favorite_genres or []
        if favorite_genres and movie.genres:
            genre_matches = len(set(favorite_genres) & set(movie.genres))
            genre_score = min(40, (genre_matches / len(favorite_genres)) * 40)
            score += genre_score
        
        # 2. User's Rating History (30 points)
        user_ratings = Rating.objects.filter(user=user)
        if user_ratings.exists():
            # Get genres from highly rated movies
            highly_rated = user_ratings.filter(score__gte=4)
            if highly_rated.exists():
                rated_genres = []
                for rating in highly_rated:
                    rated_genres.extend(rating.movie.genres)
                
                if rated_genres and movie.genres:
                    common_genres = len(set(rated_genres) & set(movie.genres))
                    rating_history_score = min(30, (common_genres / len(set(rated_genres))) * 30)
                    score += rating_history_score
        
        # 3. Movie's Overall Rating (20 points)
        # Normalize TMDb rating (0-10) to our scale (0-20)
        rating_score = (movie.vote_average / 10) * 20
        score += rating_score
        
        # 4. Movie's Popularity (10 points)
        # Normalize popularity (assuming max ~100)
        popularity_score = min(10, (movie.popularity / 100) * 10)
        score += popularity_score
        
        return round(score, 2)
    
    @staticmethod
    def _anonymous_score(movie: MovieMetadata) -> float:
        """
        Calculate score for anonymous users based on movie quality only
        """
        # 50% from rating, 50% from popularity
        rating_score = (movie.vote_average / 10) * 50
        popularity_score = min(50, (movie.popularity / 100) * 50)
        return round(rating_score + popularity_score, 2)
    
    @staticmethod
    def get_recommendations_for_user(user, limit: int = 20) -> List[Dict]:
        """
        Get personalized movie recommendations for a user
        
        Returns list of movies with match scores
        """
        # Get movies user hasn't rated
        if user.is_authenticated:
            rated_movie_ids = Rating.objects.filter(user=user).values_list('movie_id', flat=True)
            movies = MovieMetadata.objects.exclude(id__in=rated_movie_ids)
        else:
            movies = MovieMetadata.objects.all()
        
        # Get top movies by popularity first (to reduce calculation)
        movies = movies.order_by('-popularity')[:100]
        
        # Calculate match scores
        recommendations = []
        for movie in movies:
            match_score = RecommendationService.calculate_match_score(user, movie)
            recommendations.append({
                'movie': movie,
                'match_score': match_score
            })
        
        # Sort by match score and return top N
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations[:limit]
    
    @staticmethod
    def get_similar_movies(movie: MovieMetadata, limit: int = 10) -> List[MovieMetadata]:
        """
        Find movies similar to the given movie based on genres
        """
        if not movie.genres:
            return []
        
        # Find movies with overlapping genres
        similar_movies = MovieMetadata.objects.exclude(id=movie.id)
        
        # Filter by at least one matching genre
        similar = []
        for m in similar_movies:
            if m.genres and set(movie.genres) & set(m.genres):
                overlap = len(set(movie.genres) & set(m.genres))
                similar.append((m, overlap))
        
        # Sort by number of overlapping genres, then by rating
        similar.sort(key=lambda x: (x[1], x[0].vote_average), reverse=True)
        return [movie for movie, _ in similar[:limit]]
    
    @staticmethod
    def get_trending_by_genre(genre: str, limit: int = 20) -> List[MovieMetadata]:
        """
        Get trending movies in a specific genre
        """
        movies = MovieMetadata.objects.filter(
            genres__contains=[genre]
        ).order_by('-popularity', '-vote_average')[:limit]
        
        return list(movies)
    
    @staticmethod
    def get_user_statistics(user) -> Dict:
        """
        Get statistics about a user's movie watching habits
        """
        if not user.is_authenticated:
            return {}
        
        ratings = Rating.objects.filter(user=user)
        
        if not ratings.exists():
            return {
                'total_ratings': 0,
                'average_rating': 0,
                'favorite_genres': [],
                'total_watch_time': 0
            }
        
        # Calculate statistics
        stats = {
            'total_ratings': ratings.count(),
            'average_rating': round(ratings.aggregate(Avg('score'))['score__avg'], 2),
            'highest_rated': ratings.order_by('-score').first(),
            'lowest_rated': ratings.order_by('score').first(),
        }
        
        # Calculate favorite genres
        genre_counts = {}
        for rating in ratings.filter(score__gte=4):
            for genre in rating.movie.genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        stats['favorite_genres'] = [genre for genre, _ in favorite_genres]
        
        # Calculate total watch time
        rated_movies = [r.movie for r in ratings if r.movie.runtime]
        total_runtime = sum(m.runtime for m in rated_movies if m.runtime)
        stats['total_watch_time'] = total_runtime  # in minutes
        stats['total_watch_time_hours'] = round(total_runtime / 60, 1)
        
        return stats


# Singleton instance
recommendation_service = RecommendationService()