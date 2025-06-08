import json
import os
import boto3
from common import validate_token

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        game_id = event['pathParameters']['game_id']
        level_number = int(event['pathParameters']['level_number'])

        table = dynamodb.Table(os.environ['TABLE_LEVELS'])

        response = table.get_item(Key={
            'game_id': game_id,
            'level_number': level_number
        })

        item = response.get('Item')
        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Level not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(item)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
