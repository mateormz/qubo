import json
import os
import uuid
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, ensure_teacher
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

@cors_handler
def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info  # ya está formateado con respond desde common.py

        error = ensure_teacher(user_info)
        if error:
            return error  # también se espera que esté con formato estándar

        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        teacher_id = user_info['user_id']

        if not name:
            return respond(400, {'error': 'Missing required field: name'})

        table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])

        # Verificar duplicado
        existing = table.query(
            IndexName='teacher-name-index',
            KeyConditionExpression=Key('teacher_id').eq(teacher_id) & Key('name').eq(name)
        )

        if existing['Items']:
            return respond(409, {'error': 'A classroom with this name already exists for this teacher'})

        # Crear nuevo classroom
        classroom_id = str(uuid.uuid4())

        table.put_item(
            Item={
                'classroom_id': classroom_id,
                'name': name,
                'teacher_id': teacher_id,
                'created_at': event['requestContext']['requestTime'],
                'students': []
            }
        )

        return respond(201, {
            'classroom_id': classroom_id,
            'name': name,
            'teacher_id': teacher_id
        })

    except Exception as e:
        return respond(500, {'error': 'Internal Server Error', 'details': str(e)})
