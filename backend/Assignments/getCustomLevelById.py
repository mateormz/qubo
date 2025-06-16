import json
import os
import boto3
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        level_id = event['pathParameters'].get('level_id')

        if not level_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'level_id is required'})
            }

        # Recuperar el nivel personalizado por ID
        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        level_response = custom_levels_table.get_item(Key={'level_id': level_id})

        if 'Item' not in level_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Custom Level with ID {level_id} not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(convert_decimal(level_response['Item']))
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
