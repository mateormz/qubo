import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def get_questions_by_custom_level_id(event, context):
    try:
        level_id = event['pathParameters'].get('level_id')

        if not level_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'level_id is required'})
            }

        # Recuperar el nivel por ID
        custom_levels_table = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        level_response = custom_levels_table.get_item(Key={'level_id': level_id})

        if 'Item' not in level_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Custom Level with ID {level_id} not found'})
            }

        questions_ids = level_response['Item'].get('questions_ids', [])

        if not questions_ids:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'No questions found for this custom level'})
            }

        # Recuperar las preguntas asociadas
        questions_table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])
        questions_response = questions_table.batch_get_item(
            RequestItems={
                os.environ['TABLE_QUESTIONS']: {
                    'Keys': [{'question_id': qid} for qid in questions_ids]
                }
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'questions': questions_response['Responses'][os.environ['TABLE_QUESTIONS']]})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
