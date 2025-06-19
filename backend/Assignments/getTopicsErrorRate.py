import json
import os
import boto3
from collections import defaultdict
from common import validate_token, convert_decimal
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Validar token y obtener información del usuario
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info
        
        # Obtener el classroom_id directamente desde la URL
        classroom_id = event['pathParameters'].get('classroom_id')

        # Validar que exista el classroom_id
        if not classroom_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'classroom_id is required'})
            }

        # Usar scan para obtener sesiones que coincidan con classroom_id
        session_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        response = session_table.scan(
            FilterExpression=Attr('classroom_id').eq(classroom_id)
        )

        sessions = convert_decimal(response.get('Items', []))

        # Contadores para los temas
        topic_errors = defaultdict(int)
        topic_total = defaultdict(int)

        # Procesar resultados de sesiones
        for session in sessions:
            for result in session.get('results', []):
                if not result['was_correct']:  # Si la respuesta es incorrecta
                    topic_errors[result['topic']] += 1  # Incrementar errores
                topic_total[result['topic']] += 1  # Contabilizar preguntas

        # Calcular el porcentaje de error por tema
        topic_error_rate = []
        for topic, total in topic_total.items():
            errors = topic_errors.get(topic, 0)
            error_rate = errors / total if total > 0 else 0
            topic_error_rate.append({
                'topic': topic,
                'errorRate': error_rate
            })

        # Ordenar los temas por errorRate en orden descendente
        sorted_topics = sorted(topic_error_rate, key=lambda x: x['errorRate'], reverse=True)

        return {
            'statusCode': 200,
            'body': json.dumps(sorted_topics)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
