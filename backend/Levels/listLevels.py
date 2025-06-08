import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        game_id = event['pathParameters']['game_id']
        table = dynamodb.Table(os.environ['TABLE_LEVELS'])

        response = table.query(
            KeyConditionExpression=Key('game_id').eq(game_id)
        )

        levels = response.get('Items', [])

        return {
            'statusCode': 200,
            'body': json.dumps({'levels': levels})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
