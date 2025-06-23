import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from common import convert_decimal
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')

def convert_time_to_seconds(level_time):
    try:
        return int(level_time)
    except:
        return 0

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
            return respond(404, {'error': f'Classroom {classroom_id} not found'})

        students = classroom_response['Item'].get('students', [])
        if not students:
            return respond(404, {'error': 'No students found in the classroom'})

        user_ids = students if isinstance(students[0], str) else [s['S'] for s in students]

        sessions_table = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        game_sessions_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])

        total_time = 0
        total_questions = 0
        total_correct = 0
        unique_users = set()
        sessions_by_day = {}

        for user_id in user_ids:
            for table in [sessions_table, game_sessions_table]:
                response = table.query(
                    IndexName='user_id-index',
                    KeyConditionExpression=Key('user_id').eq(user_id)
                )

                for session in response.get('Items', []):
                    timestamp = session.get('timestamp')
                    level_time = session.get('level_time', 0)
                    results = session.get('results', [])

                    unique_users.add(user_id)
                    num_questions = len(results)
                    correct_answers = sum(1 for r in results if r.get('was_correct'))

                    seconds = convert_time_to_seconds(level_time)
                    total_time += seconds
                    total_questions += num_questions
                    total_correct += correct_answers

                    date_str = timestamp.split('T')[0] if timestamp else 'unknown'
                    if date_str not in sessions_by_day:
                        sessions_by_day[date_str] = {
                            'total_time_spent': 0,
                            'total_questions_answered': 0,
                            'total_correct': 0
                        }

                    sessions_by_day[date_str]['total_time_spent'] += seconds
                    sessions_by_day[date_str]['total_questions_answered'] += num_questions
                    sessions_by_day[date_str]['total_correct'] += correct_answers

        average_time_per_student = total_time // max(len(unique_users), 1)
        average_correct_rate = total_correct / total_questions if total_questions > 0 else 0

        progress_by_day = []
        for date, metrics in sorted(sessions_by_day.items()):
            q = metrics['total_questions_answered']
            c = metrics['total_correct']
            progress_by_day.append({
                'date': date,
                'total_time_spent': metrics['total_time_spent'],
                'total_questions_answered': q,
                'average_correct_rate': round(c / q, 2) if q > 0 else 0.0
            })

        result = {
            'total_questions_answered': total_questions,
            'average_time_spent_per_student': average_time_per_student,
            'average_correct_rate': round(average_correct_rate, 2),
            'progress_by_day': progress_by_day
        }

        return respond(200, convert_decimal(result))

    except Exception as e:
        print("❌ Excepción:", str(e))
        return respond(500, {'error': 'Internal server error', 'details': str(e)})
