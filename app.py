import logging
from flask import Flask, render_template, request, jsonify, send_file
import os
import csv
import scrape_maps_phones

app = Flask(__name__)
scraping_state = {'businesses': [], 'current_batch': 0, 'total_links': 0}

@app.route('/')
def index():
    """Serve the frontend HTML."""
    logging.info("Serving web interface")
    return render_template('index.html')

@app.route('/start_scrape', methods=['POST'])
def start_scrape():
    """Initialize scraping with the provided search term."""
    search_term = request.json.get('search_term')
    if not search_term:
        logging.error("No search term provided.")
        return jsonify({'error': 'Search term is required'}), 400

    logging.info(f"Starting Web Scrape for: {search_term}")
    try:
        scraping_state['businesses'] = []
        scraping_state['current_batch'] = 0
        businesses = scrape_maps_phones.main(search_term)
        if not businesses:
            logging.error("No businesses found.")
            return jsonify({'error': 'No businesses found'}), 400
        
        scraping_state['businesses'] = businesses
        scraping_state['total_links'] = len(businesses)
        logging.info(f"Collected {len(businesses)} businesses.")
        
        return jsonify({
            'status': 'ready',
            'message': f'Found {len(businesses)} businesses. Ready to process in batches.',
            'business_count': len(businesses)
        })
    except Exception as e:
        logging.error(f"Error during scrape: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scrape_batch', methods=['POST'])
def scrape_batch():
    """Process the next batch of businesses."""
    try:
        businesses = scraping_state['businesses']
        current_batch = scraping_state['current_batch']
        batch_size = 30
        
        if not businesses:
            logging.error("No businesses to process.")
            return jsonify({'error': 'No businesses available'}), 400
        
        start_idx = current_batch * batch_size
        if start_idx >= len(businesses):
            logging.info("All batches completed.")
            scrape_maps_phones.save_to_csv(businesses)
            scrape_maps_phones.save_websites_to_csv(businesses)
            results = [{
                'business_name': name,
                'website': website or 'N/A',
                'phone': phone or 'N/A'
            } for name, website, phone in businesses]
            return jsonify({
                'status': 'complete',
                'message': f'Scraping complete! Found {len([r for r in results if r["phone"] != "N/A"])} phone numbers.',
                'results': results,
                'websites_csv': '/download/websites.csv',
                'phones_csv': '/download/phones.csv'
            })
        
        logging.info(f"Processing batch {current_batch + 1} (businesses {start_idx + 1}-{min(start_idx + batch_size, len(businesses))})...")
        batch_results = businesses[start_idx:min(start_idx + batch_size, len(businesses))]
        scraping_state['current_batch'] += 1
        
        scrape_maps_phones.save_to_csv(businesses[:start_idx + len(batch_results)])
        scrape_maps_phones.save_websites_to_csv(businesses[:start_idx + len(batch_results)])
        
        results = [{
            'business_name': name,
            'website': website or 'N/A',
            'phone': phone or 'N/A'
        } for name, website, phone in businesses[:start_idx + len(batch_results)]]
        
        return jsonify({
            'status': 'batch_complete',
            'message': f'Batch {current_batch + 1} complete. Processed {len(batch_results)} businesses. Total phone numbers: {len([r for r in results if r["phone"] != "N/A"])}.',
            'results': results,
            'next_batch': current_batch + 1,
            'remaining': len(businesses) - (start_idx + batch_size),
            'total': len(businesses)
        })
    except Exception as e:
        logging.error(f"Error during batch processing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Serve CSV files for download."""
    if filename not in ['websites.csv', 'phones.csv']:
        logging.error(f"Invalid file requested: {filename}")
        return jsonify({'error': 'Invalid file'}), 400
    file_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(file_path):
        logging.error(f"{filename} not found")
        return jsonify({'error': f'{filename} not found'}), 404
    logging.info(f"Downloading {filename}...")
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    logging.info("Starting Flask server...")
    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)