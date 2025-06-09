import json
import os
import uuid
from datetime import datetime
import boto3
from common import validate_token, ensure_teacher_or_admin  # Ajusta según roles válidos

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        
        # Extraer datos del body
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        price = body.get('price')
        image_url = body.get('image_url')

        missing = [field for field in ['name', 'price', 'image_url'] if not body.get(field)]
        if missing:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Missing fields: {", ".join(missing)}'})
            }

        # Crear skin
        skin_id = str(uuid.uuid4())
        table = dynamodb.Table(os.environ['SKINS_TABLE'])

        item = {
            'skin_id': skin_id,
            'name': name,
            'price': int(price),
            'image_url': image_url,
            'created_at': datetime.utcnow().isoformat()
        }

        table.put_item(Item=item)

        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(item)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }