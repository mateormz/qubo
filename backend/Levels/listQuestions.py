import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from common import validate_token

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        topic = event['queryStringParameters'].get('topic') if event.get('queryStringParameters') else None
        game_id = event['queryStringParameters'].get('game_id') if event.get('queryStringParameters') else None

        table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])

        if topic:
            filter_expr = Attr('topic').eq(topic)
        elif game_id:
            filter_expr = Attr('game_id').eq(game_id)
        else:
            filter_expr = None

        if filter_expr:
            scan_kwargs = {'FilterExpression': filter_expr}
        else:
            scan_kwargs = {}

        response = table.scan(**scan_kwargs)

        return {
            'statusCode': 200,
            'body': json.dumps({'questions': response.get('Items', [])})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
