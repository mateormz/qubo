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

        table = dynamodb.Table(os.environ['TABLE_GAMES'])
        response = table.scan()
        games = convert_decimal(response.get('Items', []))  

        return {
            'statusCode': 200,
            'body': json.dumps({'games': games})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
