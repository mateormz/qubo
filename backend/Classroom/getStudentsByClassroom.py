import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, ensure_teacher
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

@cors_handler
def lambda_handler(event, context):
    try:
        # Validar token y rol
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_teacher(user_info)
        if error:
            return error

        # Obtener el classroom_id desde la URL
        classroom_id = event['pathParameters'].get('classroom_id')
        if not classroom_id:
            return respond(400, {'error': 'Missing required parameter: classroom_id'})

        teacher_id = user_info['user_id']
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])

        # Consultar el aula correspondiente
        response = classroom_table.get_item(
            Key={'classroom_id': classroom_id}
        )

        if 'Item' not in response:
            return respond(404, {'error': 'Classroom not found'})

        classroom = response['Item']

        # Verificar que el teacher_id coincida con el del usuario autenticado
        if classroom['teacher_id'] != teacher_id:
            return respond(403, {'error': 'Unauthorized access to this classroom'})

        # Obtener la lista de estudiantes
        students = classroom.get('students', [])

        return respond(200, {'students': students})

    except Exception as e:
        return respond(500, {'error': 'Internal Server Error', 'details': str(e)})
