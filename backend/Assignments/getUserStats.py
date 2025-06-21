import json
import os
import boto3
from datetime import datetime
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Validar token
        user_info = validate_token(event)
        if 'statusCode' in user_info:
            return user_info  # Error de token

        # Obtener user_id desde el path del evento
        user_id = event['pathParameters'].get('user_id')
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_id is required in the URL'})
            }

        # Consultar la tabla de usuarios para obtener información del usuario
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])
        user_response = user_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in user_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'User {user_id} not found'})
            }
        
        user_info = user_response['Item']
        user_name = user_info.get('name', 'N/A')  # Nombre del usuario

        # Consultar las sesiones en dev-qubo-game-sessions y dev-qubo-sessions-table
        sessions_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        game_sessions_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])

        # Consultar todos los submits del usuario
        sessions_response = sessions_table.query(
            IndexName='user_id-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )
        
        game_sessions_response = game_sessions_table.query(
            IndexName='user_id-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )

        # Sumar los tiempos jugados (level_time) y contar las preguntas respondidas
        total_time_played = 0  # En segundos
        total_questions_answered = 0
        last_active_time = None

        # Procesar las sesiones de dev-qubo-sessions-table
        for session in sessions_response.get('Items', []):
            if 'level_time' in session:
                level_time = session['level_time']
                total_time_played += convert_decimal(level_time)  # Asumiendo que level_time está en formato segundos
            if 'timestamp' in session:
                session_time = session['timestamp']
                if not last_active_time or session_time > last_active_time:
                    last_active_time = session_time
            total_questions_answered += len(session.get('results', [])) * 8  # Multiplicamos por 8 por cada submit

        # Procesar las sesiones de dev-qubo-game-sessions-table
        for game_session in game_sessions_response.get('Items', []):
            if 'level_time' in game_session:
                level_time = game_session['level_time']
                total_time_played += convert_decimal(level_time)
            if 'timestamp' in game_session:
                session_time = game_session['timestamp']
                if not last_active_time or session_time > last_active_time:
                    last_active_time = session_time
            total_questions_answered += len(game_session.get('results', [])) * 8

        # Devolver las estadísticas de usuario
        stats = {
            'user_id': user_id,
            'name': user_name,
            'total_time_played': total_time_played,  # Total tiempo jugado en segundos
            'questions_answered': total_questions_answered,
            'last_time_active': last_active_time
        }

        return {
            'statusCode': 200,
            'body': json.dumps(stats)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
