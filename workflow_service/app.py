# workflow/app.py
import os
import uuid
import requests
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://data:5001')
SERVERLESS_PROCESSING_URL = os.environ.get('SERVERLESS_PROCESSING_URL')  # 必须提供

def trigger_serverless(submission_id):
    if not SERVERLESS_PROCESSING_URL:
        logging.error("SERVERLESS_PROCESSING_URL not set")
        return
    try:
        requests.post(SERVERLESS_PROCESSING_URL, json={'submission_id': submission_id}, timeout=10)
        logging.info(f"Triggered serverless for {submission_id}")
    except requests.exceptions.Timeout:
        logging.warning(f"Serverless call timeout for {submission_id}, but may still process")
    except Exception as e:
        logging.error(f"Failed to trigger serverless: {e}")

@app.route('/submit', methods=['POST'])
def submit_event():
    event_data = request.get_json()
    if not event_data:
        return jsonify({'error': 'No data'}), 400

    submission_id = str(uuid.uuid4())
    record = {
        'id': submission_id,
        'status': 'PENDING',
        'data': event_data,
        'result': None
    }

    try:
        resp = requests.post(f'{DATA_SERVICE_URL}/submissions', json=record, timeout=5)
        if resp.status_code != 201:
            return jsonify({'error': 'Data service store failed'}), 500
    except Exception as e:
        logging.error(f"Data service error: {e}")
        return jsonify({'error': 'Cannot reach data service'}), 500

    trigger_serverless(submission_id)

    return jsonify({'submission_id': submission_id, 'status': 'processing_started'}), 202

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)