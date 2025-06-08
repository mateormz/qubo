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

        question_id = event['pathParameters']['question_id']
        table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])

        response = table.get_item(Key={'question_id': question_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Question not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(convert_decimal(item))
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
