import json
import os
import uuid
import boto3
from common import validate_token

dynamodb = boto3.resource('dynamodb')

def create_custom_question(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        if user_info.get('role') != 'teacher':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Only teachers can create custom questions'})
            }

        body = json.loads(event.get('body', '[]'))
        if not isinstance(body, list) or not body:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Body must be a non-empty list of questions'})
            }

        # Verificar que el level_id exista
        custom_levels = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        questions_table = dynamodb.Table(os.environ['TABLE_CUSTOM_QUESTIONS'])
        created = []

        for q in body:
            text = q.get('text')
            options = q.get('options')
            correct_index = q.get('correctIndex')
            topic = q.get('topic')
            level_id = q.get('level_id')

            if not all([text, options, topic, level_id]) or correct_index is None:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Each question needs text, options, correctIndex, topic, and level_id'})
                }

            # validar opciones
            if not isinstance(options, list) or len(options) < 2:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Options must be a list of at least 2 items'})
                }

            # validar level_id
            lvl = custom_levels.get_item(Key={'level_id': level_id})
            if 'Item' not in lvl:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f'Custom level {level_id} not found'})
                }

            qid = str(uuid.uuid4())
            questions_table.put_item(Item={
                'question_id': qid,
                'text': text,
                'options': options,
                'correctIndex': correct_index,
                'topic': topic,
                'level_id': level_id
            })
            created.append({'question_id': qid, 'text': text})

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Questions created', 'questions': created})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
