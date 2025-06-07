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

        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')

        # Environment variables
        try:
            user_table_name = os.environ['TABLE_USERS']
            token_table_name = os.environ['TABLE_TOKENS']
            email_index = os.environ['INDEX_EMAIL_USERS']
            print("[INFO] Environment variables loaded successfully")
        except KeyError as env_error:
            print(f"[ERROR] Missing environment variable: {str(env_error)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f"Missing environment variable: {str(env_error)}"})
            }

        user_table = dynamodb.Table(user_table_name)
        token_table = dynamodb.Table(token_table_name)

        # Parse request body
        if 'body' not in event or not event['body']:
            print("[WARNING] Request body is missing")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Request body is missing'})
            }

        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON body: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }

        role = body.get('role')
        if role not in ['student', 'teacher']:
            print("[WARNING] Invalid or missing role")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid or missing role'})
            }

        email = body.get('email')
        password = body.get('password')
        name = body.get('name')
        lastName = body.get('lastName')
        dni = body.get('dni')
        phoneNumber = body.get('phoneNumber') if role == 'teacher' else None

        # Validación de campos obligatorios
        missing_fields = []
        for field in ['email', 'password', 'name', 'lastName', 'dni']:
            if not body.get(field):
                missing_fields.append(field)
        if role == 'teacher' and not phoneNumber:
            missing_fields.append('phoneNumber')
        if missing_fields:
            print(f"[WARNING] Missing required fields: {missing_fields}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f"Missing required fields: {', '.join(missing_fields)}"})
            }

        # Check if the email is already registered
        print(f"[INFO] Checking if email is already registered: {email}")
        response = user_table.query(
            IndexName=email_index,
            KeyConditionExpression=Key('email').eq(email)
        )
        if response['Items']:
            print("[WARNING] Email is already registered")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'The email is already registered'})
            }

        # Crear usuario
        user_id = str(uuid.uuid4())
        item = {
            'user_id': user_id,
            'email': email,
            'password_hash': hash_password(password),
            'name': name,
            'lastName': lastName,
            'dni': dni,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'role': role
        }

        if role == 'student':
            item['qu_coin'] = 0
            item['streak'] = 0
        elif role == 'teacher':
            item['phoneNumber'] = phoneNumber

        print(f"[INFO] Saving user to DynamoDB: {item}")
        user_table.put_item(Item=item)

        # Crear token
        token = str(uuid.uuid4())
        expiration = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

        print(f"[INFO] Token generated: {token}, Expiration: {expiration}")
        print("[INFO] Storing token in DynamoDB")
        token_table.put_item(
            Item={
                'token': token,
                'expiration': expiration,
                'user_id': user_id
            }
        )

        print("[INFO] Returning successful response")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'token': token,
                'expires': expiration,
                'user_id': user_id
            })
        }

    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }