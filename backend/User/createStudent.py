import json
import os
import uuid
import boto3
import hashlib
from datetime import datetime
from boto3.dynamodb.conditions import Key
from common import validate_token, ensure_teacher
from cors_utils import cors_handler, respond

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@cors_handler
def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_teacher(user_info)
        if error:
            return error

        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        lastName = body.get('lastName')
        dni = body.get('dni')
        email = body.get('email')
        classroom_id = body.get('classroom_id')

        missing = [f for f in ['name', 'lastName', 'dni', 'email', 'classroom_id'] if not body.get(f)]
        if missing:
            return respond(400, {'error': f'Missing required fields: {", ".join(missing)}'})

        user_table = dynamodb.Table(os.environ['TABLE_USERS'])
        classroom_table = dynamodb.Table(os.environ['TABLE_CLASSROOMS'])

        index_name = os.environ['INDEX_EMAIL_USERS']
        response = user_table.query(
            IndexName=index_name,
            KeyConditionExpression=Key('email').eq(email)
        )
        if response.get('Items'):
            return respond(409, {'error': 'Email already in use'})

        class_result = classroom_table.get_item(Key={'classroom_id': classroom_id})
        classroom = class_result.get('Item')
        if not classroom:
            return respond(404, {'error': 'Classroom not found'})

        # Obtener lista de juegos
        try:
            list_games_function = f"{os.environ['GAMES_SERVICE_NAME']}-{os.environ['STAGE']}-{os.environ['LIST_GAMES_FUNCTION']}"
            games_response = lambda_client.invoke(
                FunctionName=list_games_function,
                InvocationType='RequestResponse',
                Payload=json.dumps({'headers': event.get('headers', {})})
            )
            games_payload = json.loads(games_response['Payload'].read())
            games_data = json.loads(games_payload['body']).get('games', []) if games_payload.get('statusCode') == 200 else []
        except Exception as e:
            games_data = []

        level_progress = {game['game_id']: 1 for game in games_data}

        # Crear estudiante
        user_id = str(uuid.uuid4())
        password_hash = hash_password(dni)

        user_item = {
            'user_id': user_id,
            'name': name,
            'lastName': lastName,
            'dni': dni,
            'email': email,
            'password_hash': password_hash,
            'role': 'student',
            'qu_coin': 0,
            'streak': 1,
            'last_login_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'classroom_id': classroom_id,
            'skinSeleccionada': "skin1",
            'skinsDesbloqueadas': ["skin1"],
            'levelProgress': level_progress,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        user_table.put_item(Item=user_item)

        classroom_table.update_item(
            Key={'classroom_id': classroom_id},
            UpdateExpression="SET students = list_append(if_not_exists(students, :empty_list), :student_id)",
            ExpressionAttributeValues={
                ':student_id': [user_id],
                ':empty_list': []
            }
        )

        return respond(201, {
            'user_id': user_id,
            'email': email,
            'role': 'student',
            'classroom_id': classroom_id,
            'skinSeleccionada': "skin1",
            'skinsDesbloqueadas': ["skin1"],
            'levelProgress': level_progress
        })

    except Exception as e:
        return respond(500, {'error': 'Internal Server Error', 'details': str(e)})
