from flask import Flask, render_template, request, jsonify, send_file
import os
import csv
import scrape_maps_phones

app = Flask(__name__)
scraping_state = {'businesses': [], 'current_batch': 0}

@app.route('/')
def index():
    """Serve the frontend HTML."""
    print("Serving web interface at http://localhost:5000")
    return render_template('index.html')

@app.route('/start_scrape', methods=['POST'])
def start_scrape():
    """Initialize scraping with the provided search term."""
    search_term = request.json.get('search_term')
    if not search_term:
        print("Error: No search term provided.")
        return jsonify({'error': 'Search term is required'}), 400

    print(f"\n=== Starting Web Scrape for: {search_term} ===")
    try:
        # Reset state
        scraping_state['businesses'] = []
        scraping_state['current_batch'] = 0
        
        # Scrape business names, URLs, and phone numbers
        print("Scraping business names, URLs, and phone numbers...")
        businesses = scrape_maps_phones.main(search_term)
        if not businesses:
            print("No businesses found.")
            return jsonify({'error': 'No businesses found'}), 400
        
        scraping_state['businesses'] = businesses
        print(f"Collected {len(businesses)} businesses.")
        
        return jsonify({
            'status': 'ready',
            'message': f'Found {len(businesses)} businesses. Ready to display phone numbers.',
            'business_count': len(businesses)
        })
    except Exception as e:
        print(f"Error during scrape: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scrape_batch', methods=['POST'])
def scrape_batch():
    """Process the next batch of businesses."""
    try:
        businesses = scraping_state['businesses']
        current_batch = scraping_state['current_batch']
        batch_size = 30
        
        if not businesses:
            print("Error: No businesses to process.")
            return jsonify({'error': 'No businesses available'}), 400
        
        start_idx = current_batch * batch_size
        if start_idx >= len(businesses):
            print("All batches completed.")
            # Save final results
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
        
        print(f"Processing batch {current_batch + 1} (businesses {start_idx + 1}-{min(start_idx + batch_size, len(businesses))})...")
        batch_results = businesses[start_idx:min(start_idx + batch_size, len(businesses))]
        scraping_state['current_batch'] += 1
        
        # Save intermediate results
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
            'remaining': len(businesses) - (start_idx + batch_size)
        })
    except Exception as e:
        print(f"Error during batch processing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Serve CSV files for download."""
    if filename not in ['websites.csv', 'phones.csv']:
        print(f"Error: Invalid file requested: {filename}")
        return jsonify({'error': 'Invalid file'}), 400
    if not os.path.exists(filename):
        print(f"Error: {filename} not found")
        return jsonify({'error': f'{filename} not found'}), 404
    print(f"Downloading {filename}...")
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    print("Starting Flask server for MapPhone Extractor...")
    app.run(debug=True, host='0.0.0.0', port=5000)