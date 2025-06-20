import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar el token
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info  # Token inválido

        # Consultar la tabla de sesiones para obtener los scores de los estudiantes
        session_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])

        # Hacer una consulta para obtener todas las sesiones de todos los estudiantes
        response = session_table.scan()

        # Extraer el score y el student_id de cada sesión
        student_scores = []

        for item in response.get('Items', []):
            # Suponiendo que `user_id` es el student_id y `score` es el puntaje
            student_scores.append({
                'student_id': item['user_id'],
                'score': item['score']
            })

        # Ordenar por score en orden descendente
        sorted_student_scores = sorted(student_scores, key=lambda x: x['score'], reverse=True)

        # Ahora obtenemos los nombres de los estudiantes si es necesario
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])
        ranked_students = []

        for student in sorted_student_scores:
            student_id = student['student_id']
            score = student['score']

            # Consultar el nombre del estudiante
            user_response = user_table.get_item(Key={'user_id': student_id})
            if 'Item' in user_response:
                name = user_response['Item'].get('name', 'Unknown')

            # Agregar al ranking
            ranked_students.append({
                'student_id': student_id,
                'name': name,
                'score': score
            })

        return {
            'statusCode': 200,
            'body': json.dumps(ranked_students)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
