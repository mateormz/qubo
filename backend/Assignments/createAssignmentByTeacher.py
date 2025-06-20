import json
import os
import uuid
import boto3
from common import validate_token
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')

@cors_handler
def lambda_handler(event, context):
    try:
        # Validar token
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        if user_info.get('role') != 'teacher':
            return respond(403, {'error': 'Only teachers can create assignments'})

        # Leer body
        body = json.loads(event.get('body', '{}'))
        classroom_id = body.get('classroom_id')
        game_name = body.get('game_name')
        level_ids = body.get('level_ids', [])

        if not classroom_id or not game_name:
            return respond(400, {'error': 'classroom_id and game_name are required'})

        if not isinstance(level_ids, list):
            return respond(400, {'error': 'level_ids must be a list'})

        # Verificar que el classroom exista
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])
        classroom_response = classroom_table.get_item(Key={'classroom_id': classroom_id})

        if 'Item' not in classroom_response:
            return respond(404, {'error': f'Classroom with ID {classroom_id} not found'})

        # Crear nueva asignación
        assignments_table = dynamodb.Table(os.environ['TABLE_ASSIGNMENTS'])
        assignment_id = str(uuid.uuid4())

        assignments_table.put_item(Item={
            'assignment_id': assignment_id,
            'teacher_id': user_info.get('user_id'),
            'classroom_id': classroom_id,
            'game_name': game_name,
            'level_ids': level_ids
        })

        return respond(201, {
            'message': 'Assignment created successfully',
            'assignment_id': assignment_id
        })

    except Exception as e:
        return respond(500, {'error': 'Internal server error', 'details': str(e)})
