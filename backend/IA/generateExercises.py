import json
import boto3
from gpt_service import GPTService
from common import validate_token, ensure_teacher

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_teacher(user_info)
        if error:
            return error

        body = json.loads(event.get('body', '{}'))
        tema = body.get('tema')

        if not tema:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required field: tema'})
            }

        gpt = GPTService()
        result = gpt.generate_exercises(tema)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }