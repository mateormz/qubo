import json
import os
import uuid
import boto3
import hashlib
from datetime import datetime
from common import validate_token, ensure_teacher

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    try:
        # Validar token
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        # Asegurar que sea teacher
        error = ensure_teacher(user_info)
        if error:
            return error

        # Parsear body
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        lastName = body.get('lastName')
        dni = body.get('dni')
        email = body.get('email')

        missing = [f for f in ['name', 'lastName', 'dni', 'email'] if not body.get(f)]
        if missing:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'Missing required fields: {", ".join(missing)}'})
            }

        table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Verificar que no exista email duplicado
        index_name = os.environ['INDEX_EMAIL_USERS']
        response = table.query(
            IndexName=index_name,
            KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
        )
        if response.get('Items'):
            return {
                'statusCode': 409,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Email already in use'})
            }

        # Crear estudiante
        user_id = str(uuid.uuid4())
        password_hash = hash_password(dni)

        item = {
            'user_id': user_id,
            'name': name,
            'lastName': lastName,
            'dni': dni,
            'email': email,
            'password_hash': password_hash,
            'role': 'student',
            'qu_coin': 0,
            'streak': 0,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        table.put_item(Item=item)

        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'user_id': user_id, 'email': email, 'role': 'student'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }