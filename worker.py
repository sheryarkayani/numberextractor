import os
import redis
from rq import Worker, Queue, Connection
from scrape_maps_phones import main

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

def run_scrape_task(search_term):
    """
    Worker function to perform the scraping task.
    """
    try:
        if not search_term or not search_term.strip():
            raise ValueError("Search term cannot be empty")
        businesses = main(search_term)
        return businesses
    except Exception as e:
        # Log the error for debugging
        import logging
        logging.error(f"Scraping failed for '{search_term}': {str(e)}")
        raise

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work() 