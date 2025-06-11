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

        body = json.loads(event.get('body', '[]'))

        if not isinstance(body, list) or len(body) == 0:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Body must be a list of questions'})
            }

        # Verificar cada pregunta
        games_table = dynamodb.Table(os.environ['TABLE_GAMES'])
        questions_table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])

        created_questions = []
        for question_data in body:
            question_text = question_data.get('text')
            options = question_data.get('options')
            correct_index = question_data.get('correctIndex')
            topic = question_data.get('topic')
            game_id = question_data.get('game_id')

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

            # Verificar si el game_id existe en la tabla de juegos
            response = games_table.get_item(Key={'game_id': game_id})
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f'Game ID {game_id} not found in the database'})
                }

            question_id = str(uuid.uuid4())
            # Crear la nueva pregunta en la tabla de preguntas
            questions_table.put_item(Item={
                'question_id': question_id,
                'text': question_text,
                'options': options,
                'correctIndex': correct_index,
                'topic': topic,
                'game_id': game_id
            })
            created_questions.append({
                'question_id': question_id,
                'text': question_text
            })
        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Questions created', 'questions': created_questions})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
