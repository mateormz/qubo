import json
import os
import uuid
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
                'body': json.dumps({'error': 'Only teachers can create questions'})
            }

        body = json.loads(event.get('body', '{}'))
        question_text = body.get('text')
        options = body.get('options')
        correct_index = body.get('correctIndex')
        topic = body.get('topic')
        game_id = body.get('game_id')

        if not all([question_text, options, topic, game_id]) or correct_index is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing fields: text, options, correctIndex, topic, game_id'})
            }

        if not isinstance(options, list) or len(options) < 2:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Options must be a list of at least 2 items'})
            }

        question_id = str(uuid.uuid4())
        table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])

        table.put_item(Item={
            'question_id': question_id,
            'text': question_text,
            'options': options,
            'correctIndex': correct_index,
            'topic': topic,
            'game_id': game_id
        })

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Question created', 'question_id': question_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
