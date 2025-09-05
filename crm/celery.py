from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

redis_url = 'redis://localhost:6379/0'
celery_app = Celery('crm', broker=redis_url, backend=redis_url)