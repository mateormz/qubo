import boto3
import hashlib
import uuid
from datetime import datetime, timedelta
import os
from boto3.dynamodb.conditions import Key
import json

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def lambda_handler(event, context):
    try:
        print("[INFO] Received event:", json.dumps(event, indent=2))

        dynamodb = boto3.resource('dynamodb')

        try:
            user_table_name = os.environ['TABLE_USERS']
            token_table_name = os.environ['TABLE_TOKENS']
            email_index = os.environ['INDEX_EMAIL_USERS']
            print("[INFO] Environment variables loaded successfully")
        except KeyError as env_error:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f"Missing environment variable: {str(env_error)}"})
            }

        user_table = dynamodb.Table(user_table_name)
        token_table = dynamodb.Table(token_table_name)

        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Request body is missing'})
            }

        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError as e:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }

        role = body.get('role')
        if role != 'teacher':
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Only teachers can register at this time'})
            }

        email = body.get('email')
        password = body.get('password')
        name = body.get('name')
        lastName = body.get('lastName')
        dni = body.get('dni')
        phoneNumber = body.get('phoneNumber')

        # Validación de campos obligatorios
        missing_fields = []
        for field in ['email', 'password', 'name', 'lastName', 'dni', 'phoneNumber']:
            if not body.get(field):
                missing_fields.append(field)

        if missing_fields:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f"Missing required fields: {', '.join(missing_fields)}"})
            }

        # Validar duplicado
        response = user_table.query(
            IndexName=email_index,
            KeyConditionExpression=Key('email').eq(email)
        )
        if response['Items']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'The email is already registered'})
            }

        # Crear usuario teacher
        user_id = str(uuid.uuid4())
        item = {
            'user_id': user_id,
            'email': email,
            'password_hash': hash_password(password),
            'name': name,
            'lastName': lastName,
            'dni': dni,
            'phoneNumber': phoneNumber,
            'role': role,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        user_table.put_item(Item=item)

        # Crear token
        token = str(uuid.uuid4())
        expiration = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

        token_table.put_item(
            Item={
                'token': token,
                'expiration': expiration,
                'user_id': user_id,
                'role': role
            }
        )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'token': token,
                'expires': expiration,
                'user_id': user_id,
                'role': role
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }