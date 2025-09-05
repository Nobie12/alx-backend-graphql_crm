## Celery background jobs

Follow these steps to run background jobs with Celery:

1. Install Redis and ensure the Redis server is running.
2. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
3. Start the Celery worker:
   ```bash
   celery -A crm worker -l info
   ```
4. Start Celery Beat (scheduler):
   ```bash
   celery -A crm beat -l info
   ```
5. Verify logs are being written to:
   ```
   /tmp/crm_report_log.txt
   ```