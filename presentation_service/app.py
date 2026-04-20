# presentation/app.py
import os
import requests
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

WORKFLOW_URL = os.environ.get('WORKFLOW_URL', 'http://workflow:5002')
DATA_SERVICE_URL = os.environ.get('DATA_SERVICE_URL', 'http://data:5001')

FORM_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Campus Buzz - Submit Event</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        input, textarea { margin: 5px 0 15px; width: 300px; display: block; }
        .error { color: red; }
        .info { color: green; }
    </style>
</head>
<body>
    <h2>📢 Submit Campus Event</h2>
    <form method="post" action="/submit">
        Title: <input type="text" name="title" required><br>
        Description (min 40 chars): <textarea name="description" rows="4" required></textarea><br>
        Location: <input type="text" name="location" required><br>
        Date (YYYY-MM-DD): <input type="text" name="date" placeholder="2025-12-31" required><br>
        Organiser: <input type="text" name="organiser" required><br>
        <input type="submit" value="Submit">
    </form>
    <hr>
    <h3>🔍 Check Submission Result</h3>
    <form method="get" action="/result">
        Submission ID: <input type="text" name="id" placeholder="e.g., 123e4567-e89b...">
        <input type="submit" value="View">
    </form>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(FORM_HTML)

@app.route('/submit', methods=['POST'])
def submit():
    event = {
        'title': request.form['title'],
        'description': request.form['description'],
        'location': request.form['location'],
        'date': request.form['date'],
        'organiser': request.form['organiser']
    }
    try:
        resp = requests.post(f'{WORKFLOW_URL}/submit', json=event, timeout=10)
        if resp.status_code != 202:
            return f'Submission failed (status {resp.status_code})', 500
        data = resp.json()
        return f'''
        <h3>✅ Submission Received</h3>
        <p>Your submission ID: <strong>{data['submission_id']}</strong></p>
        <p>Use this ID to check the result later. Background processing may take a few seconds.</p>
        <a href="/">Back</a>
        '''
    except Exception as e:
        return f'<p class="error">Error: {e}</p><a href="/">Back</a>', 500

@app.route('/result')
def result():
    submission_id = request.args.get('id')
    if not submission_id:
        return 'Missing ID', 400
    try:
        resp = requests.get(f'{DATA_SERVICE_URL}/submissions/{submission_id}', timeout=5)
        if resp.status_code != 200:
            return 'Submission not found or still processing', 404
        record = resp.json()
        result = record.get('result', {})
        status = result.get('final_status', 'PENDING')
        category = result.get('category', 'N/A')
        priority = result.get('priority', 'N/A')
        note = result.get('note', 'Processing in background...')
        return f'''
        <h3>📋 Submission Result</h3>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Priority:</strong> {priority}</p>
        <p><strong>Note:</strong> {note}</p>
        <a href="/">Back</a>
        '''
    except Exception as e:
        return f'Error: {e}', 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)