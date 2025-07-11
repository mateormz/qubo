import json
import os
import boto3
import uuid
from datetime import datetime
from common import validate_token, convert_decimal  # <- añadimos esto

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
        game_id = event['pathParameters']['game_id']
        level_number = int(event['pathParameters']['level_number'])
        body = json.loads(event.get('body', '{}'))
        responses = body.get('responses', [])

        if not isinstance(responses, list) or not responses:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid or missing responses'})
            }

        question_table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])
        session_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])

        correct_count = 0
        results = []

        for response in responses:
            question_id = response.get('questionId')
            selected_index = response.get('selectedIndex')

            question_item = question_table.get_item(Key={'question_id': question_id}).get('Item')
            if not question_item:
                continue

            correct_index = question_item['correctIndex']
            is_correct = selected_index == correct_index
            if is_correct:
                correct_count += 1

            results.append({
                'question_id': question_id,
                'was_correct': is_correct,
                'topic': question_item.get('topic', 'N/A')
            })

        passed = correct_count >= 6
        session_id = str(uuid.uuid4())

        # Guardar sesión
        session_table.put_item(Item={
            'session_id': session_id,
            'user_id': user_id,
            'game_id': game_id,
            'level_number': level_number,
            'score': correct_count,
            'passed': passed,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Si pasó, verificar y actualizar el progreso
        if passed:
            user_item = user_table.get_item(Key={'user_id': user_id}).get('Item')
            current_progress = user_item.get('levelProgress', {})
            current_level = current_progress.get(game_id, 1)

            if level_number == current_level:
                current_progress[game_id] = level_number + 1
                user_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression='SET levelProgress = :lp',
                    ExpressionAttributeValues={':lp': current_progress}
                )

        # Prepara respuesta segura para JSON
        response_data = convert_decimal({
            'sessionId': session_id,
            'score': correct_count,
            'passed': passed,
            'incorrectQuestions': [r for r in results if not r['was_correct']]
        })

        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
