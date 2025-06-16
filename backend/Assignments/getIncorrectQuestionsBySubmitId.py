# getIncorrectQuestionsBySubmitId.py

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

        session_id = event['pathParameters'].get('session_id')
        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'session_id is required'})
            }

        table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        resp = table.get_item(Key={'session_id': session_id})
        session = resp.get('Item')

        if not session:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Session {session_id} not found'})
            }

        incorrect = []
        for r in session.get('results', []):
            if not r['was_correct']:
                incorrect.append({
                    'question_id': r['question_id'],
                    'topic': r.get('topic', 'N/A'),
                    'level_id': session['level_id']
                })

        return {
            'statusCode': 200,
            'body': json.dumps({'incorrectQuestions': incorrect})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
