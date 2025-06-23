import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')

@cors_handler
def lambda_handler(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        assignment_id = event['pathParameters'].get('assignment_id')

        if not assignment_id:
            return respond(400, {'error': 'assignment_id is required'})

        # Consultar niveles personalizados por assignment_id usando GSI
        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        response = custom_levels_table.query(
            IndexName='assignment_id-index',
            KeyConditionExpression=Key('assignment_id').eq(assignment_id)
        )

        return respond(200, {'custom_levels': convert_decimal(response.get('Items', []))})

    except Exception as e:
        return respond(500, {'error': 'Internal server error', 'details': str(e)})
