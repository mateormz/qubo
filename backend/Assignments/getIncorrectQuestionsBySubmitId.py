# getIncorrectQuestionsBySubmitId.py

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal  

dynamodb = boto3.resource('dynamodb')

def get_incorrect_questions_by_submit_id(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
         session_id = event['pathParameters'].get('session_id')
        if not session_id:
            return {'statusCode':400,'body':json.dumps({'error':'session_id is required'})}

        table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        resp = table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        sessions = convert_decimal(resp.get('Items', []))
        incorrect = []

        for s in sessions:
            if s['session_id'] == submit_id:
                for r in s.get('results', []):
                    if not r['was_correct']:
                        incorrect.append({
                            'question_id': r['question_id'],
                            'topic': r.get('topic', 'N/A'),
                            'level_id': s['level_id']
                        })

        return {'statusCode': 200, 'body': json.dumps({'incorrectQuestions': incorrect})}

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error', 'details': str(e)})}
