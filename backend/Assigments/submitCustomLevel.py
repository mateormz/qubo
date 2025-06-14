# submitCustomLevel.py

import json
import os
import boto3
import uuid
from datetime import datetime
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')

def submit_custom_level(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
        level_id = event['pathParameters'].get('level_id')
        body = json.loads(event.get('body', '{}'))
        responses = body.get('responses', [])
        if not isinstance(responses, list) or not responses:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid or missing responses'})}

        # Recuperar nivel
        levels = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        lvl = levels.get_item(Key={'level_id': level_id})
        if 'Item' not in lvl:
            return {'statusCode': 404, 'body': json.dumps({'error': f'Custom level {level_id} not found'})}

        qids = lvl['Item'].get('questions_ids', [])
        # Verificar respuestas contra custom-questions
        qt = dynamodb.Table(os.environ['TABLE_CUSTOM_QUESTIONS'])
        correct = 0
        results = []
        for resp in responses:
            qid = resp.get('questionId')
            sel = resp.get('selectedIndex')
            if qid not in qids:
                continue
            item = qt.get_item(Key={'question_id': qid}).get('Item')
            if not item:
                continue
            is_corr = sel == item['correctIndex']
            if is_corr: correct += 1
            results.append({'question_id': qid, 'was_correct': is_corr, 'topic': item.get('topic','N/A')})

        passed = correct >= 6
        session_id = str(uuid.uuid4())
        # Guardar sesión
        sess = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        sess.put_item(Item={
            'session_id': session_id,
            'user_id': user_id,
            'level_id': level_id,
            'score': correct,
            'passed': passed,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Actualizar submissions en el nivel
        levels.update_item(
            Key={'level_id': level_id},
            UpdateExpression="SET submissions = list_append(submissions, :s)",
            ExpressionAttributeValues={':s': [{'user_id': user_id, 'score': correct, 'passed': passed}]}
        )

        return {
            'statusCode': 200,
            'body': json.dumps(convert_decimal({
                'sessionId': session_id,
                'score': correct,
                'passed': passed,
                'incorrectQuestions': [r for r in results if not r['was_correct']]
            }))
        }

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error', 'details': str(e)})}
