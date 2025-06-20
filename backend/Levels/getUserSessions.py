import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar el token del header
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info  # Token inválido

        # Obtener user_id desde la URL
        user_id = event['pathParameters'].get('user_id')

        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_id is required in the URL'})
            }

        # Validar que el user del token coincida con el del path
        if user_info['user_id'] != user_id:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: token does not match user_id in URL'})
            }

        # Consultar la tabla de sesiones para obtener las sesiones del usuario
        table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])

        response = table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        raw_sessions = convert_decimal(response.get('Items', []))

        # Simplificar los campos de "results" y agregar la duración
        for session in raw_sessions:
            simplified_results = []
            for r in session.get("results", []):
                simplified_results.append({
                    "question_id": r.get("question_id"),
                    "topic": r.get("topic"),
                    "was_correct": r.get("was_correct")
                })
            session["results"] = simplified_results

            # Asegurarnos de incluir la duración de la sesión (en segundos)
            session["duration_seconds"] = session.get("duration_seconds", 0)

        return {
            'statusCode': 200,
            'body': json.dumps({'sessions': raw_sessions})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
