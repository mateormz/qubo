import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        table = dynamodb.Table(os.environ['TABLE_SKINS'])
        body = json.loads(event.get('body', '{}'))

        name = body.get('name')
        description = body.get('description', '')
        price = body.get('price')
        image_url = body.get('image_url')

        # Validación básica
        if not name or price is None or not image_url:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        # Obtener el número actual de skins
        existing_skins = table.scan(ProjectionExpression="skin_id")
        count = len(existing_skins.get('Items', []))
        new_skin_id = f"skin{count + 1}"

        # Crear item
        item = {
            'skin_id': new_skin_id,
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
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }