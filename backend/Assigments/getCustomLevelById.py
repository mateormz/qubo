import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def get_custom_level_by_id(event, context):
    try:
        level_id = event['pathParameters'].get('level_id')

        if not level_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'level_id is required'})
            }

        # Recuperar el nivel personalizado por ID
        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        level_response = custom_levels_table.get_item(Key={'level_id': level_id})

        if 'Item' not in level_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Custom Level with ID {level_id} not found'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(level_response['Item'])
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
