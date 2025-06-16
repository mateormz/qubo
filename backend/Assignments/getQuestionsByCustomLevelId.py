import json
import os
import boto3
from common import validate_token
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.resource('dynamodb')
deserializer = TypeDeserializer()

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

        # Usar el cliente para batch_get_item
        client = boto3.client('dynamodb')
        resp = client.batch_get_item(
            RequestItems={
                os.environ['TABLE_CUSTOM_QUESTIONS']: {
                    'Keys': [{'question_id': {'S': qid}} for qid in qids]
                }
            }
        )

        raw_questions = resp['Responses'].get(os.environ['TABLE_CUSTOM_QUESTIONS'], [])
        questions = [ {k: deserializer.deserialize(v) for k, v in item.items()} for item in raw_questions ]

        return {'statusCode': 200, 'body': json.dumps({'questions': questions})}

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error', 'details': str(e)})}
