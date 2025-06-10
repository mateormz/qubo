import json
import os
import uuid
import boto3
from datetime import datetime
from common import validate_token

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        if user_info.get('role') != 'teacher':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Only teachers can create games'})
            }

        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        description = body.get('description')
        level_count = body.get('level_count', 0)

        if not name or not description:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields: name, description'})
            }

        game_id = str(uuid.uuid4())
        table = dynamodb.Table(os.environ['TABLE_GAMES'])

        table.put_item(Item={
            'game_id': game_id,
            'name': name,
            'description': description,
            'level_count': level_count,
            'created_at': datetime.utcnow().isoformat()
        })

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Game created',
                'game_id': game_id
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
