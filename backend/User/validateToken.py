import boto3
from datetime import datetime
import os
import json
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')

@cors_handler
def lambda_handler(event, context):
    try:
        print("[INFO] Received event:", json.dumps(event, indent=2))

        try:
            token_table_name = os.environ['TABLE_TOKENS']
            print("[INFO] Environment variable loaded successfully")
            print(f"[DEBUG] Token table name: {token_table_name}")
        except KeyError as env_error:
            return respond(500, {'error': f'Missing environment variable: {str(env_error)}'})

        table = dynamodb.Table(token_table_name)

        if not event.get('body'):
            return respond(400, {'error': 'Request body is missing'})

        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return respond(400, {'error': 'Invalid JSON in request body'})

        token = body.get('token')
        if not token:
            return respond(400, {'error': 'Token not provided'})

        print(f"[INFO] Getting token from table: {token}")
        response = table.get_item(Key={'token': token})
        token_data = response.get('Item')

        if not token_data:
            return respond(403, {'error': 'Invalid token'})

        expiration = token_data.get('expiration')
        print(f"[DEBUG] Token expiration: {expiration}")

        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > expiration:
            return respond(403, {'error': 'Token expired'})

        print("[INFO] Token is valid")

        return respond(200, {
            'message': 'Token is valid',
            'expiration': expiration,
            'user_id': token_data.get('user_id'),
            'role': token_data.get('role')
        })

    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return respond(500, {'error': 'Internal Server Error', 'details': str(e)})
