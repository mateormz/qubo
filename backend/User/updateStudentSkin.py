import json
import os
import boto3
from common import validate_token, ensure_user_ownership

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar token
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        # Asegurar que accede solo a su propia cuenta (ahora sí se espera el user_id en path)
        error = ensure_user_ownership(event, user_info['user_id'])
        if error:
            return error

        # Verificar que el usuario sea estudiante
        if user_info.get('role') != 'student':
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Only students can update their skin'})
            }

        # Extraer el índice de skin del body
        body = json.loads(event.get('body', '{}'))
        skin_selected = body.get('skin_selected')

        if skin_selected is None:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing skin_selected'})
            }

        # Obtener el user_id del path para realizar la actualización
        user_id = event['pathParameters']['user_id']
        table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Actualizar la skin seleccionada
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET skin_selected = :s',
            ExpressionAttributeValues={':s': int(skin_selected)}
        )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'Skin updated successfully'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }