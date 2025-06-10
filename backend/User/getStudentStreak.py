import json
import os
import boto3
from common import validate_token, ensure_user_ownership, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar token
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        # Asegurar que accede solo a su propia cuenta
        error = ensure_user_ownership(event, user_info['user_id'])
        if error:
            return error

        # Verificar que el usuario sea estudiante
        if user_info.get('role') != 'student':
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Only students can access their streak'})
            }

        # Obtener el user_id del path
        user_id = event['pathParameters']['user_id']
        table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Obtener datos del estudiante
        response = table.get_item(Key={'user_id': user_id})
        student = response.get('Item')

        if not student:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Student not found'})
            }

        streak = student.get('streak', 0)
        last_login_date = student.get('last_login_date', None)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'streak': convert_decimal(streak),
                'last_login_date': last_login_date
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }
