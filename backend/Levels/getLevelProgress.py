import json
import os
import boto3
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])

        user_item = user_table.get_item(Key={'user_id': user_id}).get('Item')
        if not user_item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'User not found'})
            }

        level_progress = user_item.get('levelProgress', {})
        level_progress = convert_decimal(level_progress)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'user_id': user_id,
                'levelProgress': level_progress
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
