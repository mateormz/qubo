# getQuestionsByCustomLevelId.py

import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def get_questions_by_custom_level_id(event, context):
    try:
        level_id = event['pathParameters'].get('level_id')
        if not level_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'level_id is required'})}

        # Recuperar el nivel
        levels = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        lvl = levels.get_item(Key={'level_id': level_id})
        if 'Item' not in lvl:
            return {'statusCode': 404, 'body': json.dumps({'error': f'Custom Level {level_id} not found'})}

        qids = lvl['Item'].get('questions_ids', [])
        if not qids:
            return {'statusCode': 404, 'body': json.dumps({'error': 'No questions for this level'})}

        # Recuperar preguntas de custom-questions
        qt = dynamodb.Table(os.environ['TABLE_CUSTOM_QUESTIONS'])
        resp = qt.batch_get_item(
            RequestItems={os.environ['TABLE_CUSTOM_QUESTIONS']: {'Keys': [{'question_id': q} for q in qids]}}
        )
        questions = resp['Responses'][os.environ['TABLE_CUSTOM_QUESTIONS']]

        return {'statusCode': 200, 'body': json.dumps({'questions': questions})}

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error', 'details': str(e)})}
