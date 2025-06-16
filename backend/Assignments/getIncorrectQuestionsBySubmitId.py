import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
        session_id = event['pathParameters'].get('session_id')

        if not session_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'session_id is required'})}

        table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        session = table.get_item(Key={'session_id': session_id})

        if 'Item' not in session:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Session not found'})}

        session_data = convert_decimal(session['Item'])
        incorrect_results = [r for r in session_data.get('results', []) if not r['was_correct']]

        if not incorrect_results:
            return {'statusCode': 200, 'body': json.dumps({'incorrectQuestions': []})}

        question_ids = [r['question_id'] for r in incorrect_results]

        # Obtener preguntas completas
        question_table = os.environ['TABLE_CUSTOM_QUESTIONS']
        response = dynamodb_client.batch_get_item(
            RequestItems={
                question_table: {
                    'Keys': [{'question_id': {'S': qid}} for qid in question_ids]
                }
            }
        )

        questions_data = {
            q['question_id']['S']: {
                'text': q['text']['S'],
                'options': [o['S'] for o in q['options']['L']]
            }
            for q in response['Responses'].get(question_table, [])
        }

        enriched = []
        for result in incorrect_results:
            qid = result['question_id']
            qdata = questions_data.get(qid)
            if not qdata:
                continue
            enriched.append({
                'question_id': qid,
                'topic': result.get('topic', 'N/A'),
                'level_id': session_data['level_id'],
                'text': qdata['text'],
                'options': qdata['options'],
                'selectedIndex': result.get('selectedIndex', -1)
            })

        return {'statusCode': 200, 'body': json.dumps({'incorrectQuestions': enriched})}

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error', 'details': str(e)})}
