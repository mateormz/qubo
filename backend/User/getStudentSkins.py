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

        if user_info.get('role') != 'student':
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Only students can access their skins'})
            }

        user_id = event['pathParameters']['user_id']
        table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Obtener al estudiante
        response = table.get_item(Key={'user_id': user_id})
        student = response.get('Item')

        if not student:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Student not found'})
            }

        # Convertir Decimals
        student = convert_decimal(student)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'skin_selected': student.get('skinSeleccionada', "skin1"),
                'skins_unlocked': student.get('skinsDesbloqueadas', ["skin1"])
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }