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

        if user_info.get('role') != 'teacher':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Only teachers can create levels'})
            }

        body = json.loads(event.get('body', '{}'))
        game_id = body.get('game_id')
        level_number = body.get('level_number')
        questions = body.get('questions')  # list of question IDs

        if not game_id or level_number is None or not isinstance(questions, list) or len(questions) != 8:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'game_id, level_number and 8 questions are required'})
            }

        table = dynamodb.Table(os.environ['TABLE_LEVELS'])

        table.put_item(Item={
            'game_id': game_id,
            'level_number': level_number,
            'questions': questions
        })

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Level created successfully'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
