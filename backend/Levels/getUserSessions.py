import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal  

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
        table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])

        response = table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'sessions': convert_decimal(response.get('Items', []))})  
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
