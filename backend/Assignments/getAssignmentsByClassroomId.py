import json
import os
import boto3
from common import validate_token

dynamodb = boto3.resource('dynamodb')

def get_assignments_by_classroom_id(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        # Verificar que el usuario sea profesor
        if user_info.get('role') != 'teacher':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Only teachers can view assignments'})
            }

        body = json.loads(event.get('body', '{}'))
        classroom_id = body.get('classroom_id')

        if not classroom_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'classroom_id is required'})
            }

        # Obtener todas las asignaciones asociadas a un aula (classroom_id)
        assignments_table = dynamodb.Table(os.environ['TABLE_ASSIGNMENTS'])
        response = assignments_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('classroom_id').eq(classroom_id)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'assignments': response.get('Items', [])})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
