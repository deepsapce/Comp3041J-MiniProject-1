import json
import os
import requests
import base64
from datetime import datetime

def parse_event(event):
    if isinstance(event, bytes):
        event = event.decode('utf-8')
    if isinstance(event, str):
        try:
            event = json.loads(event)
        except:
            return {}

    if not isinstance(event, dict):
        return {}

    if 'submission_id' in event:
        return event

    body = event.get('body')
    if body is None:
        return {}

    if isinstance(body, dict):
        return body

    if event.get('isBase64Encoded', False):
        body = base64.b64decode(body).decode('utf-8')
    elif isinstance(body, bytes):
        body = body.decode('utf-8')

    try:
        return json.loads(body)
    except:
        return {}

def apply_rules(submission_record):
    data = submission_record.get('data', {})

    required_fields = ['title', 'description', 'location', 'date', 'organiser']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return {
            'final_status': 'INCOMPLETE',
            'category': None,
            'priority': None,
            'note': f'Missing required field(s): {", ".join(missing)}'
        }

    text = (data.get('title', '') + ' ' + data.get('description', '')).lower()
    if any(kw in text for kw in ['career', 'internship', 'recruitment']):
        category = 'OPPORTUNITY'
        priority = 'HIGH'
    elif any(kw in text for kw in ['workshop', 'seminar', 'lecture']):
        category = 'ACADEMIC'
        priority = 'MEDIUM'
    elif any(kw in text for kw in ['club', 'society', 'social']):
        category = 'SOCIAL'
        priority = 'NORMAL'
    else:
        category = 'GENERAL'
        priority = 'NORMAL'

    date_valid = False
    desc_valid = False
    errors = []

    try:
        datetime.strptime(data['date'], '%Y-%m-%d')
        date_valid = True
    except (ValueError, TypeError):
        errors.append('Invalid date format (must be YYYY-MM-DD)')

    if len(data.get('description', '')) >= 40:
        desc_valid = True
    else:
        errors.append('Description must be at least 40 characters')

    if date_valid and desc_valid:
        final_status = 'APPROVED'
        note = f'Approved as {category} with {priority} priority.'
    else:
        final_status = 'NEEDS REVISION'
        note = '; '.join(errors)

    return {
        'final_status': final_status,
        'category': category,
        'priority': priority,
        'note': note
    }

def handler(event, context):
    data = parse_event(event)
    submission_id = data.get('submission_id')
    if not submission_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing submission_id'})
        }

    data_service_url = os.environ.get('DATA_SERVICE_URL')
    if not data_service_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'DATA_SERVICE_URL not set'})
        }

    try:
        resp = requests.get(f"{data_service_url}/submissions/{submission_id}", timeout=10)
        if resp.status_code != 200:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Submission not found: {submission_id}'})
            }
        record = resp.json()
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Data service error: {str(e)}'})
        }

    result = apply_rules(record)

    update_url = os.environ.get('RESULT_UPDATE_FUNCTION_URL')
    if not update_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'RESULT_UPDATE_FUNCTION_URL not set'})
        }

    try:
        upd_resp = requests.post(update_url, json={'submission_id': submission_id, 'result': result}, timeout=10)
        if upd_resp.status_code == 200:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'updated': True})
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Update failed: {upd_resp.text}'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }