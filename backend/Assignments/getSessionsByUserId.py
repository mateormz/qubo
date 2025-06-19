import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar token del header
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info  # Error de token

        # Obtener user_id desde la URL
        user_id_from_path = event['pathParameters'].get('user_id')
        if not user_id_from_path:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_id is required in the URL'})
            }

        # Validar que el user del token coincida con el del path
        if user_info['user_id'] != user_id_from_path:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Forbidden: token does not match user_id in URL'})
            }

        session_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])

        response = session_table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id_from_path)
        )

        raw_sessions = convert_decimal(response.get('Items', []))

        # Simplificar los campos de "results"
        for session in raw_sessions:
            simplified_results = []
            for r in session.get("results", []):
                simplified_results.append({
                    "question_id": r.get("question_id"),
                    "topic": r.get("topic"),
                    "was_correct": r.get("was_correct")
                })
            session["results"] = simplified_results

        return {
            'statusCode': 200,
            'body': json.dumps({'sessions': raw_sessions})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
