import json
import boto3
from gpt_service import GPTService
from common import validate_token

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        body = json.loads(event.get('body', '{}'))
        mensaje = body.get('mensaje')

        if not mensaje:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required field: mensaje'})
            }

        gpt = GPTService()
        respuesta = gpt.chat_with_qubo(mensaje)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'respuesta': respuesta})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }
