import json
import os
import boto3
from common import validate_token, ensure_user_ownership

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar token y asegurar propiedad
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_user_ownership(event, user_info['user_id'])
        if error:
            return error

        # Solo estudiantes pueden desbloquear skins
        if user_info.get('role') != 'student':
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Only students can unlock skins'})
            }

        # Extraer skin_id del body
        body = json.loads(event.get('body', '{}'))
        skin_id = body.get('skin_id')

        if not skin_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing skin_id'})
            }

        user_id = event['pathParameters']['user_id']
        table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Obtener skins actuales
        response = table.get_item(Key={'user_id': user_id})
        student = response.get('Item')

        if not student:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Student not found'})
            }

        unlocked = student.get('skinsDesbloqueadas', [])

        if skin_id in unlocked:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'message': 'Skin already unlocked'})
            }

        # Actualizar con la nueva skin
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET skinsDesbloqueadas = list_append(if_not_exists(skinsDesbloqueadas, :empty), :new)',
            ExpressionAttributeValues={
                ':new': [skin_id],
                ':empty': []
            }
        )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': f'Skin {skin_id} unlocked successfully'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }