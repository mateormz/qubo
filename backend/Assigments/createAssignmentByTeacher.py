import json
import os
import boto3
from common import validate_token

dynamodb = boto3.resource('dynamodb')

def create_assignment_by_teacher(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        if user_info.get('role') != 'teacher':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Only teachers can create assignments'})
            }

        body = json.loads(event.get('body', '{}'))
        classroom_id = body.get('classroom_id')
        game_name = body.get('game_name')
        questions = body.get('questions')

        if not classroom_id or not game_name or not isinstance(questions, list) or len(questions) < 1:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'classroom_id, game_name and at least 1 question are required'})
            }

        # Verificar que el classroom_id exista
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])
        classroom_response = classroom_table.get_item(Key={'classroom_id': classroom_id})

        if 'Item' not in classroom_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Classroom with ID {classroom_id} not found'})
            }

        # Crear un nuevo assignment en la tabla de asignaciones
        assignments_table = dynamodb.Table(os.environ['TABLE_ASSIGNMENTS'])
        assignment_id = str(boto3.utils.uuid.uuid4())  # Crear ID único para el assignment

        assignments_table.put_item(Item={
            'assignment_id': assignment_id,
            'teacher_id': user_info.get('user_id'),
            'classroom_id': classroom_id,
            'game_name': game_name,
            'questions': questions
        })

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Assignment created successfully', 'assignment_id': assignment_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
