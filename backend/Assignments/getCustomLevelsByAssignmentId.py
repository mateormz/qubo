import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        assignment_id = event['pathParameters'].get('assignment_id')

        if not assignment_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'assignment_id is required'})
            }

        # Recuperar los niveles personalizados por assignment_id usando el índice
        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        response = custom_levels_table.query(
            IndexName='assignment_id-index',
            KeyConditionExpression=Key('assignment_id').eq(assignment_id)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'custom_levels': convert_decimal(response.get('Items', []))})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
