import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def get_custom_levels_by_assignment_id(event, context):
    try:
        assignment_id = event['pathParameters'].get('assignment_id')

        if not assignment_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'assignment_id is required'})
            }

        # Recuperar los niveles personalizados por assignment_id
        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        response = custom_levels_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('assignment_id').eq(assignment_id)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'custom_levels': response.get('Items', [])})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
