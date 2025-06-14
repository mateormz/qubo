import json
import os
import boto3
from common import validate_token

dynamodb = boto3.resource('dynamodb')

def create_custom_level(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        # Verificar que el usuario sea profesor
        if user_info.get('role') != 'teacher':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Only teachers can create custom levels'})
            }

        body = json.loads(event.get('body', '{}'))
        assignment_id = body.get('assignment_id')
        game_type = body.get('game_type')  # Tipo de juego (ej. "GameJump")
        description = body.get('description')
        name = body.get('name')
        questions_ids = body.get('questions_ids')  # Lista de IDs de las preguntas

        if not assignment_id or not game_type or not name or not isinstance(questions_ids, list) or len(questions_ids) == 0:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'assignment_id, game_type, name, and questions_ids are required'})
            }

        # Verificar que el assignment_id exista
        assignments_table = dynamodb.Table(os.environ['TABLE_ASSIGNMENTS'])
        assignment_response = assignments_table.get_item(Key={'assignment_id': assignment_id})

        if 'Item' not in assignment_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Assignment with ID {assignment_id} not found'})
            }

        # Crear un nuevo nivel personalizado
        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        level_id = str(boto3.utils.uuid.uuid4())  # Crear ID único para el nivel

        custom_levels_table.put_item(Item={
            'level_id': level_id,
            'assignment_id': assignment_id,
            'game_type': game_type,
            'description': description,
            'name': name,
            'questions_ids': questions_ids,
            'submissions': []  # Nueva lista de submissions vacía
        })

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Custom level created successfully', 'level_id': level_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
