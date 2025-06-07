import json
import os
import uuid
import boto3
from decimal import Decimal
from common import validate_token, ensure_teacher

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar token
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        # Asegurar que sea teacher
        error = ensure_teacher(user_info)
        if error:
            return error

        # Extraer campos del body
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        teacher_id = user_info['user_id']

        if not name:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required field: name'})
            }

        # Guardar en DynamoDB
        classroom_id = str(uuid.uuid4())
        table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])

        table.put_item(
            Item={
                'classroom_id': classroom_id,
                'name': name,
                'teacher_id': teacher_id,
                'created_at': event['requestContext']['requestTime'],
                'students': []
            }
        )

        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'classroom_id': classroom_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }