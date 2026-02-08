from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, MovieMetadata


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a new User is created
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile whenever the User is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(pre_save, sender=MovieMetadata)
def normalize_movie_genres(sender, instance, **kwargs):
    """
    Automatically lowercase movie genres before saving to ensure
    consistent cross-database filtering (PostgreSQL/SQLite).
    """
    if isinstance(instance.genres, list):
        instance.genres = [g.lower() for g in instance.genres if isinstance(g, str)]


@receiver(pre_save, sender=UserProfile)
def normalize_profile_genres(sender, instance, **kwargs):
    """
    Automatically lowercase favorite genres in the profile before saving.
    """
    if isinstance(instance.favorite_genres, list):
        instance.favorite_genres = [g.lower() for g in instance.favorite_genres if isinstance(g, str)]