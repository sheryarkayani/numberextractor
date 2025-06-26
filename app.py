import logging
from flask import Flask, render_template, request, jsonify, send_file
import os
import redis
from rq import Queue

# App setup
app = Flask(__name__)

# Redis and RQ setup
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)
q = Queue(connection=conn)

@app.route('/')
def index():
    """Serve the frontend HTML."""
    logging.info("Serving web interface")
    return render_template('index.html')

@app.route('/start_scrape', methods=['POST'])
def start_scrape():
    """Enqueue a scraping job."""
    search_term = request.json.get('search_term')
    if not search_term:
        return jsonify({'error': 'Search term is required'}), 400

    logging.info(f"Enqueuing scrape for: {search_term}")
    try:
        # Import the task function here to avoid circular imports
        from worker import run_scrape_task
        job = q.enqueue(run_scrape_task, search_term, job_timeout='30m')
        return jsonify({'job_id': job.get_id()})
    except Exception as e:
        logging.error(f"Error enqueuing job: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scrape_status/<job_id>')
def scrape_status(job_id):
    """Check the status of a scraping job and get results."""
    job = q.fetch_job(job_id)
    if job is None:
        return jsonify({'status': 'not_found'}), 404

    if job.is_finished:
        businesses = job.result
        if not businesses:
            return jsonify({'status': 'complete', 'result': []})
        
        results = [{
            'business_name': name,
            'website': website or 'N/A',
            'phone': phone or 'N/A'
        } for name, website, phone in businesses]

        return jsonify({
            'status': 'complete',
            'result': results,
            'websites_csv': '/download/websites.csv',
            'phones_csv': '/download/phones.csv'
        })
    elif job.is_failed:
        error_message = str(job.exc_info) if job.exc_info else "Unknown error occurred"
        return jsonify({'status': 'failed', 'error': error_message}), 500
    else:
        return jsonify({'status': 'running'})

@app.route('/download/<filename>')
def download_file(filename):
    """Serve CSV files for download."""
    if filename not in ['websites.csv', 'phones.csv']:
        return jsonify({'error': 'Invalid file'}), 400
    file_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(file_path):
        return jsonify({'error': f'{filename} not found'}), 404
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
import logging

# Configure logging at module level
logging.basicConfig(level=logging.INFO)

# App setup
app = Flask(__name__)

# ... rest of the code ...

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)