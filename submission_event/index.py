import json
import os
import requests
import base64

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

def handler(event, context):
    data = parse_event(event)
    submission_id = data.get('submission_id')
    if not submission_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing submission_id'})
        }

    processing_url = os.environ.get('PROCESSING_FUNCTION_URL')
    if not processing_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'PROCESSING_FUNCTION_URL not set'})
        }

    try:
        resp = requests.post(processing_url, json={'submission_id': submission_id}, timeout=30)
        if resp.status_code == 200:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'result': 'processing started'})
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Processing failed: {resp.text}'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }