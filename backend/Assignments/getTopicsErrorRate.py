import json
import os
import boto3
from collections import defaultdict
from boto3.dynamodb.conditions import Attr
from common import validate_token, convert_decimal
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')

@cors_handler
def lambda_handler(event, context):
    try:
        # Validar token y obtener información del usuario
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info
    
        # Obtener el classroom_id desde la URL
        classroom_id = event['pathParameters'].get('classroom_id')

        if not classroom_id:
            return respond(400, {'error': 'classroom_id is required'})

        # Escanear sesiones que coincidan con el classroom_id
        session_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        response = session_table.scan(
            FilterExpression=Attr('classroom_id').eq(classroom_id)
        )

        sessions = convert_decimal(response.get('Items', []))

        # Contadores por tópico
        topic_errors = defaultdict(int)
        topic_total = defaultdict(int)

        for session in sessions:
            for result in session.get('results', []):
                if not result['was_correct']:
                    topic_errors[result['topic']] += 1
                topic_total[result['topic']] += 1

        topic_error_rate = []
        for topic, total in topic_total.items():
            errors = topic_errors.get(topic, 0)
            error_rate = errors / total if total > 0 else 0
            topic_error_rate.append({
                'topic': topic,
                'errorRate': error_rate
            })

        sorted_topics = sorted(topic_error_rate, key=lambda x: x['errorRate'], reverse=True)

        return respond(200, sorted_topics)

    except Exception as e:
        return respond(500, {'error': 'Internal server error', 'details': str(e)})
