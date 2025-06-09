import json
import os
import boto3
from common import validate_token, ensure_user_ownership, convert_decimal
from decimal import Decimal

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
                'body': json.dumps({'error': 'Only students can update their coins'})
            }

        # Extraer parámetros del body
        body = json.loads(event.get('body', '{}'))
        operation = body.get('operation')
        amount = body.get('amount')

        if operation not in ('add', 'subtract') or not isinstance(amount, int):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid request: must provide operation (add|subtract) and integer amount'})
            }

        # Obtener el user_id del path
        user_id = event['pathParameters']['user_id']
        table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Obtener qu_coin actual
        response = table.get_item(Key={'user_id': user_id})
        student = response.get('Item')

        if not student:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Student not found'})
            }

        current_coins = student.get('qu_coin', 0)

        # Si es Decimal, convertir a int
        if isinstance(current_coins, Decimal):
            current_coins = int(current_coins) if current_coins % 1 == 0 else float(current_coins)

        # Aplicar operación
        if operation == 'add':
            new_coins = current_coins + amount
        elif operation == 'subtract':
            if current_coins < amount:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Insufficient coins'})
                }
            new_coins = current_coins - amount

        # Actualizar en la base de datos
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET qu_coin = :q',
            ExpressionAttributeValues={':q': Decimal(new_coins)}
        )

        # Devolver respuesta, convirtiendo el Decimal
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Coins updated successfully',
                'qu_coin': convert_decimal(new_coins)
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }
