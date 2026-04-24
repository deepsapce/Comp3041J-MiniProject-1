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
    result = data.get('result')
    if not submission_id or result is None:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing submission_id or result'})
        }

    data_service_url = os.environ.get('DATA_SERVICE_URL')
    if not data_service_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'DATA_SERVICE_URL not set'})
        }

    try:
        resp = requests.put(
            f"{data_service_url}/submissions/{submission_id}",
            json={'result': result},
            timeout=10
        )
        if resp.status_code == 200:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'updated'})
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Update HTTP {resp.status_code}: {resp.text}'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }