import json
import boto3
from gpt_service import GPTService
from common import validate_token

lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        # Validar autenticación
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        body = json.loads(event.get('body', '{}'))

        # Validar campos necesarios
        question_text = body.get('text')
        topic = body.get('topic')
        correct_answer = body.get('correctAnswer')

        missing = [key for key in ['text', 'topic', 'correctAnswer'] if not body.get(key)]
        if missing:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f"Missing required fields: {', '.join(missing)}"})
            }

        gpt = GPTService()
        guide = gpt.generate_resolution_guide(question_text, topic, correct_answer)

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(guide)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }
