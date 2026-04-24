# data/app.py
import os
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

# 内存存储
store = {}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/submissions', methods=['POST'])
def create_submission():
    data = request.get_json()
    submission_id = data.get('id')
    if not submission_id:
        return jsonify({'error': 'Missing id'}), 400
    store[submission_id] = data
    return jsonify({'status': 'created', 'id': submission_id}), 201

@app.route('/submissions/<submission_id>', methods=['GET'])
def get_submission(submission_id):
    record = store.get(submission_id)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(record)

@app.route('/submissions/<submission_id>', methods=['PUT'])
def update_submission(submission_id):
    data = request.get_json()
    if submission_id not in store:
        return jsonify({'error': 'Not found'}), 404
    store[submission_id].update(data)
    return jsonify(store[submission_id])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)