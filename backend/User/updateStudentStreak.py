import json
import os
import boto3
from common import validate_token, ensure_user_ownership, convert_decimal
from datetime import datetime, timedelta
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
                'body': json.dumps({'error': 'Only students can update their streak'})
            }

        # Obtener el user_id del path
        user_id = event['pathParameters']['user_id']
        table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Obtener streak actual y last_login_date
        response = table.get_item(Key={'user_id': user_id})
        student = response.get('Item')

        if not student:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Student not found'})
            }

        # Leer campos
        current_streak = student.get('streak', 0)
        last_login_str = student.get('last_login_date', None)

        # Obtener fecha actual (UTC)
        today_str = datetime.utcnow().strftime('%Y-%m-%d')
        today_date = datetime.strptime(today_str, '%Y-%m-%d').date()

        # Calcular nueva racha
        if last_login_str:
            last_login_date = datetime.strptime(last_login_str, '%Y-%m-%d').date()
            delta_days = (today_date - last_login_date).days

            if delta_days == 0:
                # Mismo día, no se suma racha
                new_streak = current_streak
            elif delta_days == 1:
                # Día siguiente → +1 racha
                new_streak = current_streak + 1
            else:
                # Se rompió la racha
                new_streak = 1
        else:
            # Primer login
            new_streak = 1

        # Actualizar en la base de datos
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET streak = :s, last_login_date = :d',
            ExpressionAttributeValues={
                ':s': Decimal(new_streak),
                ':d': today_str
            }
        )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Streak updated successfully',
                'streak': convert_decimal(new_streak),
                'last_login_date': today_str
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }
