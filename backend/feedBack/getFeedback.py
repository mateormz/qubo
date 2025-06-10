import json
import boto3
import os
from common import validate_token

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Autenticación
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        session_id = event.get('pathParameters', {}).get('session_id')
        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing session_id in path'})
            }

        feedback_table = dynamodb.Table(os.environ['TABLE_FEEDBACK'])
        result = feedback_table.get_item(Key={'session_id': session_id}).get('Item')

        if not result:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Feedback not found for the given session_id'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({
                "session_id": result['session_id'],
                "feedback": result['feedback']
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
