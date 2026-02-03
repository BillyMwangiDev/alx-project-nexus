import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('nexus_movie_api')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all registered Django apps
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    'sync-trending-movies-daily': {
        'task': 'apps.movies_api.tasks.sync_trending_movies',
        'schedule': crontab(hour=0, minute=0),  # Run at Midnight daily
    },
    'update-popularity-weekly': {
        'task': 'apps.movies_api.tasks.bulk_update_popularity',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday at 3 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')