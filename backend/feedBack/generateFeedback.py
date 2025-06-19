import json
import boto3
import os
from datetime import datetime
from common import validate_token

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Autenticación
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('session_id')
        session_type = body.get('type', 'Levels')  # Nuevo parámetro con default

        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing session_id'})
            }

        # Elegir tabla de sesión según tipo
        if session_type == 'Assignments':
            session_table_name = os.environ['TABLE_ASSIGNMENT_SESSIONS']
            get_question_function = f"{os.environ['TEACHER_SERVICE_NAME']}-{os.environ['STAGE']}-getCustomQuestionById"
        else:
            session_table_name = os.environ['TABLE_GAME_SESSIONS']
            get_question_function = f"{os.environ['SERVICE_NAME']}-{os.environ['STAGE']}-getQuestion"

        session_table = dynamodb.Table(session_table_name)
        session_data = session_table.get_item(Key={'session_id': session_id}).get('Item')

        if not session_data:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Session not found'})
            }

        incorrect_questions = [q for q in session_data.get('results', []) if not q['was_correct']]

        if not incorrect_questions:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No incorrect questions. Nothing to generate.'})
            }

        feedback_items = []

        # Lambda para IA
        generate_guide_function = f"{os.environ['IA_SERVICE_NAME']}-{os.environ['STAGE']}-generateGuide"

        for q in incorrect_questions:
            question_id = q['question_id']
            topic = q.get('topic', 'N/A')

            # Obtener pregunta de Lambda correspondiente
            question_payload = {
                "pathParameters": {"question_id": question_id},
                "headers": event.get("headers", {})
            }

            question_response = lambda_client.invoke(
                FunctionName=get_question_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(question_payload)
            )

            question_body = json.loads(question_response['Payload'].read())
            if question_body.get('statusCode') != 200:
                continue

            question_data = json.loads(question_body['body'])
            question_text = question_data['text']
            options = question_data['options']
            correct_index = question_data['correctIndex']
            correct_answer = options[correct_index]

            # Generar guía con IA
            guide_payload = {
                "headers": event.get("headers", {}),
                "body": json.dumps({
                    "text": question_text,
                    "topic": topic,
                    "correctAnswer": correct_answer
                })
            }

            guide_response = lambda_client.invoke(
                FunctionName=generate_guide_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(guide_payload)
            )

            guide_body = json.loads(guide_response['Payload'].read())
            if guide_body.get('statusCode') != 200:
                continue

            guide = json.loads(guide_body['body'])

            feedback_items.append({
                "question_id": question_id,
                "topic": topic,
                "text": question_text,
                "guide": guide
            })

        # Guardar en feedback
        feedback_table = dynamodb.Table(os.environ['TABLE_FEEDBACK'])
        feedback_table.put_item(Item={
            "session_id": session_id,
            "user_id": user_id,
            "feedback": feedback_items,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            'statusCode': 200,
            'body': json.dumps({
                "session_id": session_id,
                "feedback": feedback_items
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
