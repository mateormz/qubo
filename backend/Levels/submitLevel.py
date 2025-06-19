import json
import os
import boto3
import uuid
from datetime import datetime
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        print("📥 Evento recibido:", json.dumps(event))

        # Validar token
        user_info = validate_token(event, lambda_client)
        print("🔑 Token validado. user_info:", user_info)

        if 'statusCode' in user_info:
            print("❌ Token inválido. Retornando:", user_info)
            return user_info

        user_id = user_info['user_id']
        game_id = event['pathParameters']['game_id']
        level_number = int(event['pathParameters']['level_number'])

        print(f"👤 user_id: {user_id} | 🕹️ game_id: {game_id} | 🎮 level_number: {level_number}")

        body = json.loads(event.get('body', '{}'))
        responses = body.get('responses', [])

        print(f"📝 Total respuestas recibidas: {len(responses)}")

        if not isinstance(responses, list) or not responses:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid or missing responses'})
            }

        question_table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])
        session_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])

        print("📦 Tablas DynamoDB obtenidas correctamente.")

        correct_count = 0
        results = []

        for i, response in enumerate(responses):
            question_id = response.get('question_id')
            selected_index = response.get('selectedIndex')

            print(f"🔍 [{i}] Revisando pregunta: {question_id} - respuesta seleccionada: {selected_index}")

            if not question_id:
                print("⚠️ question_id está vacío o None. Saltando.")
                continue

            try:
                question_item = question_table.get_item(Key={'question_id': question_id}).get('Item')
            except Exception as qe:
                print(f"❌ Error al obtener la pregunta {question_id} de la tabla: {qe}")
                continue

            if not question_item:
                print(f"⚠️ No se encontró la pregunta {question_id} en la tabla.")
                continue

            correct_index = question_item.get('correctIndex')
            is_correct = selected_index == correct_index

            print(f"✅ correct_index: {correct_index} | {'✔️ Correcto' if is_correct else '❌ Incorrecto'}")

            if is_correct:
                correct_count += 1

            results.append({
                'question_id': question_id,
                'was_correct': is_correct,
                'topic': question_item.get('topic', 'N/A')
            })

        passed = correct_count >= 6
        session_id = str(uuid.uuid4())

        print(f"📊 Resultado: {correct_count} correctas | {'🟢 Aprobado' if passed else '🔴 Reprobado'}")
        print("💾 Guardando sesión:", session_id)

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

        if passed:
            print("🔄 Verificando progreso del usuario...")

            user_item = user_table.get_item(Key={'user_id': user_id}).get('Item')
            if not user_item:
                print("⚠️ Usuario no encontrado en la tabla. No se actualiza progreso.")
            else:
                current_progress = user_item.get('levelProgress', {})
                current_level = current_progress.get(game_id, 1)

                print(f"📈 Progreso actual: nivel {current_level}")

                if level_number == current_level:
                    current_progress[game_id] = level_number + 1
                    user_table.update_item(
                        Key={'user_id': user_id},
                        UpdateExpression='SET levelProgress = :lp',
                        ExpressionAttributeValues={':lp': current_progress}
                    )
                    print(f"✅ Progreso actualizado a nivel {level_number + 1}")

        response_data = convert_decimal({
            'sessionId': session_id,
            'score': correct_count,
            'passed': passed,
            'incorrectQuestions': [r for r in results if not r['was_correct']]
        })

        print("📤 Respuesta final:", response_data)

        return {
            'statusCode': 200,
            'body': json.dumps(response_data)
        }

    except Exception as e:
        print("❌ Excepción general:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
