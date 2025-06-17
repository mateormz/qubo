import json
import os
import boto3
from cors_utils import cors_handler, respond
from common import validate_token, ensure_teacher
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

@cors_handler
def lambda_handler(event, context):
    try:
        # 1) Validar token y rol
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_teacher(user_info)
        if error:
            return error

        # 2) Obtener classroom_id
        classroom_id = event['pathParameters'].get('classroom_id')
        if not classroom_id:
            return respond(400, {'error': 'Missing required parameter: classroom_id'})

        # 3) Leer la clase
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])
        classroom_result = classroom_table.get_item(Key={'classroom_id': classroom_id})
        classroom = classroom_result.get('Item')
        if not classroom:
            return respond(404, {'error': 'Classroom not found'})

        classroom_name = classroom.get('name')
        student_ids    = classroom.get('students', [])
        if not student_ids:
            return respond(200, {'classroom_name': classroom_name, 'students': []})

        # 4) Obtener detalles de cada estudiante
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])
        student_details = []

        for student_id in student_ids:
            student_result = user_table.get_item(Key={'user_id': student_id})
            student = student_result.get('Item')
            if not student:
                continue

            student_details.append({
                'user_id':            student['user_id'],
                'name':               student['name'],
                'lastName':           student['lastName'],
                'email':              student['email'],
                'dni':                student['dni'],
                'classroom_id':       student.get('classroom_id'),
                'created_at':         student.get('created_at'),
                'skinSeleccionada':   student.get('skinSeleccionada')  # <-- añadido
            })

        # 5) Devolver response
        return respond(200, {
            'classroom_name': classroom_name,
            'students':       student_details
        })

    except Exception as e:
        return respond(500, {'error': 'Internal Server Error', 'details': str(e)})
