web: gunicorn --bind 0.0.0.0:$PORT app:app
worker: rq worker --url $REDIS_URL