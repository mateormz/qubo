import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Validación de token (sin restricción de rol)
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        # Obtener classroom_id desde query parameters
        classroom_id = event.get('queryStringParameters', {}).get('classroom_id')

        if not classroom_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'classroom_id is required'})
            }

        # Consultar por el índice global
        assignments_table = dynamodb.Table(os.environ['TABLE_ASSIGNMENTS'])
        response = assignments_table.query(
            IndexName='classroom_id-index',
            KeyConditionExpression=Key('classroom_id').eq(classroom_id)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'assignments': response.get('Items', [])})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
