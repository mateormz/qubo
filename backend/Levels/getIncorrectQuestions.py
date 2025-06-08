import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token

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

        sessions = response.get('Items', [])
        incorrect_questions = []

        for session in sessions:
            for result in session.get('results', []):
                if not result['was_correct']:
                    incorrect_questions.append({
                        'question_id': result['question_id'],
                        'topic': result.get('topic', 'N/A'),
                        'game_id': session['game_id'],
                        'level_number': session['level_number']
                    })

        return {
            'statusCode': 200,
            'body': json.dumps({'incorrectQuestions': incorrect_questions})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
