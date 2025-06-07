import json
import os
import uuid
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, ensure_teacher

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_teacher(user_info)
        if error:
            return error

        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        teacher_id = user_info['user_id']

        if not name:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing required field: name'})
            }

        table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])

        # 4. Verificar que no exista un aula con el mismo nombre para ese teacher
        existing = table.query(
            IndexName='teacher-name-index',
            KeyConditionExpression=Key('teacher_id').eq(teacher_id) & Key('name').eq(name)
        )

        if existing['Items']:
            return {
                'statusCode': 409,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'A classroom with this name already exists for this teacher'})
            }

        # 5. Crear classroom
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

        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'classroom_id': classroom_id,
                'name': name,
                'teacher_id': teacher_id
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }