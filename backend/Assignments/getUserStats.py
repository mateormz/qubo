import json
import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')

def convert_time_to_seconds(level_time):
    if level_time:
        try:
            return int(level_time)
        except ValueError:
            print(f"⚠️ Error al convertir level_time: {level_time}")
            return 0
    return 0

def get_user_stats(user_id):
    print(f"🔍 Obteniendo estadísticas para el usuario: {user_id}")

    user_table = dynamodb.Table(os.environ['TABLE_USERS'])
    user_response = user_table.get_item(Key={'user_id': user_id})
    
    if 'Item' not in user_response:
        print(f"⚠️ Usuario con ID {user_id} no encontrado.")
        return None
    
    user_info = user_response['Item']
    user_name = user_info.get('name', 'N/A')

    sessions_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
    game_sessions_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])

    sessions_response = sessions_table.query(
        IndexName='user_id-index',
        KeyConditionExpression=Key('user_id').eq(user_id)
    )

    game_sessions_response = game_sessions_table.query(
        IndexName='user_id-index',
        KeyConditionExpression=Key('user_id').eq(user_id)
    )

    total_time_played = 0
    total_submits = 0
    last_active_time = None

    for session in sessions_response.get('Items', []):
        if 'level_time' in session:
            total_time_played += convert_time_to_seconds(session['level_time'])
        if 'timestamp' in session:
            if not last_active_time or session['timestamp'] > last_active_time:
                last_active_time = session['timestamp']
        if 'results' in session:
            total_submits += 1

    for game_session in game_sessions_response.get('Items', []):
        if 'level_time' in game_session:
            total_time_played += convert_time_to_seconds(game_session['level_time'])
        if 'timestamp' in game_session:
            if not last_active_time or game_session['timestamp'] > last_active_time:
                last_active_time = game_session['timestamp']
        if 'results' in game_session:
            total_submits += 1

    total_questions_answered = total_submits * 8

    stats = {
        'user_id': user_id,
        'name': user_name,
        'total_time_played': total_time_played,
        'questions_answered': total_questions_answered,
        'last_time_active': last_active_time
    }

    print(f"🔚 Estadísticas obtenidas para {user_id}: {stats}")
    return stats

@cors_handler
def lambda_handler(event, context):
    try:
        classroom_id = event['pathParameters'].get('classroom_id')
        if not classroom_id:
            return respond(400, {'error': 'classroom_id is required in the URL'})

        print(f"🔍 Consultando aula con ID: {classroom_id}")

        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])
        classroom_response = classroom_table.get_item(Key={'classroom_id': classroom_id})

        if 'Item' not in classroom_response:
            print(f"⚠️ Aula con ID {classroom_id} no encontrada.")
            return respond(404, {'error': f'Classroom {classroom_id} not found'})

        students = classroom_response['Item'].get('students', [])
        print(f"📚 Estudiantes encontrados: {students}")

        if not students:
            return respond(404, {'error': 'No students found in the classroom'})

        user_ids = students if isinstance(students[0], str) else [student['S'] for student in students]
        print(f"🔍 user_ids extraídos: {user_ids}")

        all_stats = []
        for user_id in user_ids:
            print(f"📊 Obteniendo estadísticas para el estudiante {user_id}")
            student_stats = get_user_stats(user_id)
            if student_stats:
                all_stats.append(student_stats)

        return respond(200, {
            'classroom_id': classroom_id,
            'students_stats': all_stats
        })

    except Exception as e:
        print("❌ Excepción general:", str(e))
        return respond(500, {'error': 'Internal server error', 'details': str(e)})
