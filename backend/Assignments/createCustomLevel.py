import json
import os
import uuid
import boto3
from common import validate_token

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        if user_info.get('role') != 'teacher':
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Only teachers can create custom levels'})
            }

        body = json.loads(event.get('body', '{}'))
        assignment_id = body.get('assignment_id')
        game_type = body.get('game_type')
        description = body.get('description')
        name = body.get('name')
        questions_ids = body.get('questions_ids')

        if not assignment_id or not game_type or not name or not isinstance(questions_ids, list):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'assignment_id, game_type, name, and questions_ids (as list) are required'})
            }

        assignments_table = dynamodb.Table(os.environ['TABLE_ASSIGNMENTS'])
        assignment_response = assignments_table.get_item(Key={'assignment_id': assignment_id})

        if 'Item' not in assignment_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Assignment with ID {assignment_id} not found'})
            }

        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        level_id = str(uuid.uuid4())

        custom_levels_table.put_item(Item={
            'level_id': level_id,
            'assignment_id': assignment_id,
            'game_type': game_type,
            'description': description,
            'name': name,
            'questions_ids': questions_ids,
            'submissions': []
        })

        assignments_table.update_item(
            Key={'assignment_id': assignment_id},
            UpdateExpression="SET level_ids = list_append(if_not_exists(level_ids, :empty_list), :new_level)",
            ExpressionAttributeValues={
                ':new_level': [level_id],
                ':empty_list': []
            }
        )

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Custom level created successfully', 'level_id': level_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
