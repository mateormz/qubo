import json
import os
import boto3
from datetime import datetime
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')

def convert_time_to_seconds(level_time):
    """
    Convierte el tiempo en formato 'str' a un número de segundos.
    Si el 'level_time' es un número en formato cadena, lo convertimos a int.
    """
    if level_time:
        try:
            # Si level_time es un número en formato cadena, lo convertimos a int
            return int(level_time)
        except ValueError:
            print(f"⚠️ Error al convertir level_time: {level_time}")
            return 0
    return 0

def get_user_stats(user_id):
    """
    Obtiene las estadísticas para un usuario dado su user_id.
    """
    user_table = dynamodb.Table(os.environ['TABLE_USERS'])
    user_response = user_table.get_item(Key={'user_id': user_id})
    
    if 'Item' not in user_response:
        print(f"⚠️ Usuario con ID {user_id} no encontrado.")
        return None  # Si no se encuentra el usuario, devolvemos None
    
    user_info = user_response['Item']
    user_name = user_info.get('name', 'N/A')  # Nombre del usuario

    sessions_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
    game_sessions_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])

    sessions_response = sessions_table.query(
        IndexName='user_id-index',
        KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
    )

    game_sessions_response = game_sessions_table.query(
        IndexName='user_id-index',
        KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
    )

    total_time_played = 0  # En segundos
    total_questions_answered = 0
    last_active_time = None

    # Procesar las sesiones de dev-qubo-sessions-table
    for session in sessions_response.get('Items', []):
        if 'level_time' in session:
            level_time = session['level_time']
            total_time_played += convert_time_to_seconds(level_time)  # Convertimos level_time a segundos
        if 'timestamp' in session:
            session_time = session['timestamp']
            if not last_active_time or session_time > last_active_time:
                last_active_time = session_time
        total_questions_answered += len(session.get('results', [])) * 8  # Multiplicamos por 8 por cada submit

    # Procesar las sesiones de dev-qubo-game-sessions-table
    for game_session in game_sessions_response.get('Items', []):
        if 'level_time' in game_session:
            level_time = game_session['level_time']
            total_time_played += convert_time_to_seconds(level_time)
        if 'timestamp' in game_session:
            session_time = game_session['timestamp']
            if not last_active_time or session_time > last_active_time:
                last_active_time = session_time
        total_questions_answered += len(game_session.get('results', [])) * 8

    stats = {
        'user_id': user_id,
        'name': user_name,
        'total_time_played': total_time_played,  # Total tiempo jugado en segundos
        'questions_answered': total_questions_answered,
        'last_time_active': last_active_time
    }

    return stats

def lambda_handler(event, context):
    try:
        classroom_id = event['pathParameters'].get('classroom_id')
        if not classroom_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'classroom_id is required in the URL'})
            }

        print(f"🔍 Consultando aula con ID: {classroom_id}")

        # Consultar la tabla de aulas para obtener los estudiantes
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])
        classroom_response = classroom_table.get_item(Key={'classroom_id': classroom_id})

        if 'Item' not in classroom_response:
            print(f"⚠️ Aula con ID {classroom_id} no encontrada.")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Classroom {classroom_id} not found'})
            }

        # Obtener la lista de estudiantes (con los user_id)
        students = classroom_response['Item'].get('students', [])
        print(f"📚 Estudiantes encontrados: {students}")

        if not students:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'No students found in the classroom'})
            }

        # Extraer solo los user_id de los estudiantes
        user_ids = [student['S'] for student in students]  # Extraemos el valor de "S" (user_id)

        # Obtener estadísticas para cada estudiante
        all_stats = []
        for user_id in user_ids:
            print(f"📊 Obteniendo estadísticas para el estudiante {user_id}")
            student_stats = get_user_stats(user_id)
            if student_stats:
                all_stats.append(student_stats)

        return {
            'statusCode': 200,
            'body': json.dumps({'classroom_id': classroom_id, 'students_stats': all_stats})
        }

    except Exception as e:
        print("❌ Excepción general:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
