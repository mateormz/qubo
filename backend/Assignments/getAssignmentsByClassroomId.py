import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')

@cors_handler
def lambda_handler(event, context):
    try:
        # Validar token (sin restricción de rol)
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        # Obtener classroom_id desde los parámetros de query
        classroom_id = event.get('queryStringParameters', {}).get('classroom_id')

        if not classroom_id:
            return respond(400, {'error': 'classroom_id is required'})

        # Consultar la tabla de asignaciones por classroom_id
        assignments_table = dynamodb.Table(os.environ['TABLE_ASSIGNMENTS'])
        response = assignments_table.query(
            IndexName='classroom_id-index',
            KeyConditionExpression=Key('classroom_id').eq(classroom_id)
        )

        return respond(200, {'assignments': response.get('Items', [])})

    except Exception as e:
        return respond(500, {'error': 'Internal server error', 'details': str(e)})
