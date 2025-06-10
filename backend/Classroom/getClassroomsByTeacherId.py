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

        teacher_id = user_info['user_id']
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])

        # Consultar aulas por teacher_id usando GSI
        response = classroom_table.query(
            IndexName='teacher-name-index',
            KeyConditionExpression=Key('teacher_id').eq(teacher_id)
        )

        classrooms = response.get('Items', [])

        return respond(200, classrooms)

    except Exception as e:
        return respond(500, {'error': 'Internal Server Error', 'details': str(e)})
