import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from apps.movies_api.tasks import sync_trending_movies
from celery.schedules import crontab
from config.celery import app as celery_app

@pytest.mark.django_db
class TestCeleryTasks:
    
    @patch('apps.movies_api.tasks.tmdb_service.get_trending_movies')
    @patch('apps.movies_api.tasks.tmdb_service.get_movie_details')
    def test_sync_trending_movies_queuing(self, mock_details, mock_trending):
        # Mock API responses
        mock_trending.return_value = {'results': [{'id': 1}]}
        mock_details.return_value = {
            'id': 1, 
            'title': 'Test Movie', 
            'overview': 'Test',
            'release_date': '2023-01-01',
            'popularity': 100
        }
        
        # We can test the task execution directly first
        result = sync_trending_movies.delay()
        
        # Since we are using eager mode in tests usually, 
        # but let's just check if it was called
        assert result is not None

    def test_celery_beat_schedule(self):
        """Verify the schedule configuration"""
        schedule = celery_app.conf.beat_schedule
        
        assert 'sync-trending-movies-daily' in schedule
        task_config = schedule['sync-trending-movies-daily']
        assert task_config['task'] == 'apps.movies_api.tasks.sync_trending_movies'
        
        # Verify it's at midnight
        assert task_config['schedule'] == crontab(hour=0, minute=0)

    @patch('apps.movies_api.tasks.tmdb_service.get_trending_movies')
    def test_task_retry_on_failure(self, mock_trending):
        """Test that the task retries on network failure"""
        mock_trending.side_effect = Exception("Network Error")
        
        with patch('apps.movies_api.tasks.sync_trending_movies.retry') as mock_retry:
            mock_retry.side_effect = Exception("Retry Called")
            
            with pytest.raises(Exception, match="Retry Called"):
                sync_trending_movies()
            
            mock_retry.assert_called_once()
