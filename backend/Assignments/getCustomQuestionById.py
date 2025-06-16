import json
import os
import boto3
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Validar token (sin restricción de rol)
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        # Obtener question_id desde el path
        question_id = event['pathParameters'].get('question_id')

        if not question_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'question_id is required'})
            }

        # Buscar pregunta en la tabla
        questions_table = dynamodb.Table(os.environ['TABLE_CUSTOM_QUESTIONS'])
        response = questions_table.get_item(Key={'question_id': question_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Question with ID {question_id} not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(convert_decimal(response['Item']))
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
