from django.db.models import Avg, Count, Q
from django.db import connection
from django.core.cache import cache
from apps.movies_api.models import MovieMetadata, Rating, UserProfile
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service for generating personalized movie recommendations
    """
    
    @staticmethod
    def calculate_match_score(user, movie: MovieMetadata) -> float:
        """
        Calculate how well a movie matches a user's preferences
        """
        if not user.is_authenticated:
            return RecommendationService._anonymous_score(movie)
        
        try:
            profile = user.profile
        except Exception:
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
            # Selection of highly rated genres
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
        rating_score = (movie.vote_average / 10) * 20
        score += rating_score
        
        # 4. Movie's Popularity (10 points)
        popularity_score = min(10, (movie.popularity / 100) * 10)
        score += popularity_score
        
        return round(score, 2)
    
    @staticmethod
    def _anonymous_score(movie: MovieMetadata) -> float:
        """
        Calculate score for anonymous users based on movie quality only
        """
        rating_score = (movie.vote_average / 10) * 50
        popularity_score = min(50, (movie.popularity / 100) * 50)
        return round(rating_score + popularity_score, 2)
    
    @staticmethod
    def get_recommendations_for_user(user, limit: int = 20) -> List[Dict]:
        """
        Get personalized movie recommendations for a user.
        Caches results for 15 minutes to improve performance.
        """
        user_id = user.id if user.is_authenticated else 'anonymous'
        cache_key = f"recommendations:user:{user_id}:limit:{limit}"
        
        try:
            cached_recommendations = cache.get(cache_key)
            if cached_recommendations is not None:
                logger.debug(f"Cache hit for recommendations: {cache_key}")
                return cached_recommendations
        except Exception as e:
            logger.error(f"Redis error (cache.get recommendations): {e}")

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
        results = recommendations[:limit]
        
        # Cache results for 15 minutes
        try:
            cache.set(cache_key, results, timeout=900)
            logger.debug(f"Cached recommendations for user {user_id}")
        except Exception as e:
            logger.error(f"Redis error (cache.set recommendations): {e}")
            
        return results
    
    @staticmethod
    def get_similar_movies(movie: MovieMetadata, limit: int = 10) -> List[MovieMetadata]:
        """
        Find movies similar to the given movie based on genres.
        Caches results for 24 hours.
        """
        cache_key = f"similar_movies:movie:{movie.id}:limit:{limit}"
        
        try:
            cached_similar = cache.get(cache_key)
            if cached_similar is not None:
                return cached_similar
        except Exception as e:
            logger.error(f"Redis error (cache.get similar_movies): {e}")

        if not movie.genres:
            return []
        
        similar_movies = MovieMetadata.objects.exclude(id=movie.id)
        similar = []
        for m in similar_movies:
            if m.genres and set(movie.genres) & set(m.genres):
                overlap = len(set(movie.genres) & set(m.genres))
                similar.append((m, overlap))
        
        similar.sort(key=lambda x: (x[1], x[0].vote_average), reverse=True)
        results = [movie for movie, _ in similar[:limit]]
        
        try:
            cache.set(cache_key, results, timeout=86400)
        except Exception as e:
            logger.error(f"Redis error (cache.set similar_movies): {e}")
            
        return results
    
    @staticmethod
    def get_trending_by_genre(genre: str, limit: int = 20) -> List[MovieMetadata]:
        """
        Get trending movies in a specific genre.
        Caches results for 1 hour.
        """
        cache_key = f"trending:genre:{genre}:limit:{limit}"
        
        try:
            cached_trending = cache.get(cache_key)
            if cached_trending is not None:
                return cached_trending
        except Exception as e:
            logger.error(f"Redis error (cache.get trending_by_genre): {e}")

        if connection.features.supports_json_field_contains:
            movies = MovieMetadata.objects.filter(
                genres__contains=[genre]
            ).order_by('-popularity', '-vote_average')[:limit]
            results = list(movies)
        else:
            # SQLite doesn't support JSONField contains lookups; fall back to Python filter
            all_movies = MovieMetadata.objects.all()
            filtered = [m for m in all_movies if m.genres and genre in m.genres]
            filtered.sort(key=lambda m: (-m.popularity, -m.vote_average))
            results = filtered[:limit]
        
        try:
            cache.set(cache_key, results, timeout=3600)
        except Exception as e:
            logger.error(f"Redis error (cache.set trending_by_genre): {e}")
            
        return results
    
    @staticmethod
    def get_user_statistics(user) -> Dict:
        """
        Get statistics about a user's movie watching habits.
        Caches for 5 minutes.
        """
        if not user.is_authenticated:
            return {}
        
        cache_key = f"user_stats:user:{user.id}"
        
        try:
            cached_stats = cache.get(cache_key)
            if cached_stats is not None:
                return cached_stats
        except Exception as e:
            logger.error(f"Redis error (cache.get user_stats): {e}")

        ratings = Rating.objects.filter(user=user)
        
        if not ratings.exists():
            return {
                'total_ratings': 0,
                'average_rating': 0,
                'favorite_genres': [],
                'total_watch_time': 0
            }
        
        stats = {
            'total_ratings': ratings.count(),
            'average_rating': round(ratings.aggregate(Avg('score'))['score__avg'], 2),
            'highest_rated': ratings.order_by('-score').first(),
            'lowest_rated': ratings.order_by('score').first(),
        }
        
        genre_counts = {}
        for rating in ratings.filter(score__gte=4):
            for genre in rating.movie.genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        stats['favorite_genres'] = [genre for genre, _ in favorite_genres]
        
        rated_movies = [r.movie for r in ratings if r.movie.runtime]
        total_runtime = sum(m.runtime for m in rated_movies if m.runtime)
        stats['total_watch_time'] = total_runtime
        stats['total_watch_time_hours'] = round(total_runtime / 60, 1)
        
        try:
            cache.set(cache_key, stats, timeout=300)
        except Exception as e:
            logger.error(f"Redis error (cache.set user_stats): {e}")
            
        return stats


# Singleton instance
recommendation_service = RecommendationService()
