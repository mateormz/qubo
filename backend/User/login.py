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

        try:
            user_table_name = os.environ['TABLE_USERS']
            token_table_name = os.environ['TABLE_TOKENS']
            email_index = os.environ['INDEX_EMAIL_USERS']
        except KeyError as env_error:
            return respond(500, {"error": f"Missing environment variable: {str(env_error)}"})

        user_table = dynamodb.Table(user_table_name)
        token_table = dynamodb.Table(token_table_name)

        if 'body' not in event or not event['body']:
            return respond(400, {"error": "Request body is missing"})

        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return respond(400, {"error": "Invalid JSON in request body"})

        email = body.get('email')
        password = body.get('password')

        if not all([email, password]):
            return respond(400, {"error": "Missing required fields"})

        hashed_password = hash_password(password)

        response = user_table.query(
            IndexName=email_index,
            KeyConditionExpression=Key('email').eq(email)
        )

        if not response['Items']:
            return respond(403, {"error": "Invalid credentials"})

        user = response['Items'][0]

        if user['password_hash'] != hashed_password:
            return respond(403, {"error": "Invalid credentials"})

        user_id = user['user_id']
        role = user.get('role', 'unknown')

        token = str(uuid.uuid4())
        expiration = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

        token_table.put_item(Item={
            'token': token,
            'expiration': expiration,
            'user_id': user_id,
            'role': role
        })

        return respond(200, {
            'token': token,
            'expires': expiration,
            'user_id': user_id,
            'role': role
        })

    except Exception as e:
        return respond(500, {"error": "Internal Server Error", "details": str(e)})
