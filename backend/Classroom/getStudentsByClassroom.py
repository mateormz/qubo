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
        # Validate token and ensure the user is a teacher
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_teacher(user_info)
        if error:
            return error

        # Get classroom_id from the path parameters
        classroom_id = event['pathParameters'].get('classroom_id')

        if not classroom_id:
            return respond(400, {'error': 'Missing required parameter: classroom_id'})

        # Query the classroom table to get the classroom details
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])
        classroom_result = classroom_table.get_item(Key={'classroom_id': classroom_id})

        classroom = classroom_result.get('Item')

        if not classroom:
            return respond(404, {'error': 'Classroom not found'})

        # Get the class name
        classroom_name = classroom.get('name')

        # Get the list of student IDs from the classroom's students attribute
        student_ids = classroom.get('students', [])

        if not student_ids:
            return respond(200, {'classroom_name': classroom_name, 'students': []})

        # Query the users table to get detailed student info
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])

        # Fetch details for each student ID
        student_details = []
        for student_id in student_ids:
            student_result = user_table.get_item(Key={'user_id': student_id})
            student = student_result.get('Item')

            if student:
                student_details.append({
                    'user_id': student['user_id'],
                    'name': student['name'],
                    'lastName': student['lastName'],
                    'email': student['email'],
                    'dni': student['dni'],
                    'classroom_id': student['classroom_id'],
                    'created_at': student['created_at']
                })

        return respond(200, {'classroom_name': classroom_name, 'students': student_details})

    except Exception as e:
        return respond(500, {'error': 'Internal Server Error', 'details': str(e)})
