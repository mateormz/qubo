import json
import os
import boto3
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        session_id = event['pathParameters'].get('session_id')

        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'session_id is required'})
            }

        # Recuperar la sesión de resultados por ID
        session_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        session_response = session_table.get_item(Key={'session_id': session_id})

        if 'Item' not in session_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Session with ID {session_id} not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(convert_decimal(session_response['Item']))
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
