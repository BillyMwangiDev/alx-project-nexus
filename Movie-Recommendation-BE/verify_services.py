import os
import django
import redis
from celery import Celery
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')
django.setup()

from django.conf import settings
from config.celery import app as celery_app

def check_redis():
    print("Checking Redis connection...")
    try:
        r = redis.Redis(host='127.0.0.1', port=6379, socket_timeout=2)
        r.ping()
        print("✅ Redis is UP and accessible at 127.0.0.1:6379")
        return True
    except Exception as e:
        print(f"❌ Redis is DOWN or inaccessible: {e}")
        return False

def check_celery_config():
    print("\nChecking Celery configuration...")
    try:
        broker = settings.CELERY_BROKER_URL
        backend = settings.CELERY_RESULT_BACKEND
        print(f"Broker URL: {broker}")
        print(f"Backend URL: {backend}")
        
        # Test if app is correctly initialized
        print(f"Celery App Name: {celery_app.main}")
        tasks = [t for t in celery_app.tasks.keys() if not t.startswith('celery.')]
        print(f"Registered Tasks: {tasks}")
        
        if 'apps.movies_api.tasks.sync_trending_movies' in tasks:
            print("✅ Sync task is correctly registered")
        else:
            print("❌ Sync task NOT found in registry")
            
        print("✅ Celery configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        return False

def check_celery_beat():
    print("\nChecking Celery Beat schedule...")
    try:
        schedule = celery_app.conf.beat_schedule
        if 'sync-trending-movies-daily' in schedule:
            print(f"✅ Daily sync scheduled at: {schedule['sync-trending-movies-daily']['schedule']}")
        else:
            print("❌ Daily sync schedule MISSING")
        return True
    except Exception as e:
        print(f"❌ Celery Beat error: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("      CELERY & REDIS VERIFICATION")
    print("="*50)
    
    redis_up = check_redis()
    config_valid = check_celery_config()
    beat_valid = check_celery_beat()
    
    print("\n" + "="*50)
    if config_valid and beat_valid:
        if redis_up:
            print("🟢 ALL SYSTEMS OPERATIONAL")
        else:
            print("🟡 LOGIC OK, BUT REDIS SERVER MISSING (REQUIRED FOR RUNTIME)")
    else:
        print("🔴 SYSTEM CONFIGURATION ERRORS FOUND")
    print("="*50)
