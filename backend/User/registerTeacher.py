import boto3
import hashlib
import uuid
from datetime import datetime, timedelta
import os
from boto3.dynamodb.conditions import Key
import json

from cors_utils import cors_handler, respond


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@cors_handler
def lambda_handler(event, context):
    try:
        print("[INFO] Received event:", json.dumps(event, indent=2))

        dynamodb = boto3.resource('dynamodb')

        # Carga de variables de entorno
        try:
            user_table_name  = os.environ['TABLE_USERS']
            token_table_name = os.environ['TABLE_TOKENS']
            email_index      = os.environ['INDEX_EMAIL_USERS']
        except KeyError as env_error:
            return respond(500, {"error": f"Missing environment variable: {str(env_error)}"})

        user_table  = dynamodb.Table(user_table_name)
        token_table = dynamodb.Table(token_table_name)

        # Verifica que exista body
        if 'body' not in event or not event['body']:
            return respond(400, {"error": "Request body is missing"})

        # Parse JSON
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return respond(400, {"error": "Invalid JSON in request body"})

        # Solo teachers
        if body.get('role') != 'teacher':
            return respond(403, {"error": "Only teachers can register at this time"})

        # Campos obligatorios
        missing = [f for f in ['email','password','name','lastName','dni','phoneNumber'] if not body.get(f)]
        if missing:
            return respond(400, {"error": f"Missing required fields: {', '.join(missing)}"})

        email       = body['email']
        password    = body['password']
        name        = body['name']
        lastName    = body['lastName']
        dni         = body['dni']
        phoneNumber = body['phoneNumber']

        # Evitar duplicados
        resp = user_table.query(
            IndexName=email_index,
            KeyConditionExpression=Key('email').eq(email)
        )
        if resp.get('Items'):
            return respond(400, {"error": "The email is already registered"})

        # Crear usuario
        user_id = str(uuid.uuid4())
        user_table.put_item(Item={
            'user_id': user_id,
            'email': email,
            'password_hash': hash_password(password),
            'name': name,
            'lastName': lastName,
            'dni': dni,
            'phoneNumber': phoneNumber,
            'role': body['role'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # Crear token
        token      = str(uuid.uuid4())
        expiration = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        token_table.put_item(Item={
            'token': token,
            'expiration': expiration,
            'user_id': user_id,
            'role': body['role']
        })

        return respond(200, {
            'token': token,
            'expires': expiration,
            'user_id': user_id,
            'role': body['role']
        })

    except Exception as e:
        return respond(500, {"error": "Internal Server Error", "details": str(e)})
