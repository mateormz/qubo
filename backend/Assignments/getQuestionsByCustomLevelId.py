import json
import os
import boto3
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
dynamo_client = boto3.client('dynamodb')  # Este sí tiene batch_get_item

def lambda_handler(event, context):
    try:
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info

        level_id = event['pathParameters'].get('level_id')
        if not level_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'level_id is required'})}

        # Recuperar el nivel
        levels = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        lvl = levels.get_item(Key={'level_id': level_id})
        if 'Item' not in lvl:
            return {'statusCode': 404, 'body': json.dumps({'error': f'Custom Level {level_id} not found'})}

        qids = lvl['Item'].get('questions_ids', [])
        if not qids:
            return {'statusCode': 404, 'body': json.dumps({'error': 'No questions for this level'})}

        # Recuperar preguntas usando batch_get_item con el cliente
        table_name = os.environ['TABLE_CUSTOM_QUESTIONS']
        keys = [{'question_id': {'S': qid}} for qid in qids]

        resp = dynamo_client.batch_get_item(
            RequestItems={
                table_name: {
                    'Keys': keys
                }
            }
        )

        raw_questions = resp['Responses'].get(table_name, [])
        # Convertir Decimals a float/int si es necesario
        questions = convert_decimal(raw_questions)

        return {
            'statusCode': 200,
            'body': json.dumps({'questions': questions})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
