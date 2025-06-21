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
        level_time = body.get('level_time', '')  # Nuevo campo

        print(f"📝 Total respuestas recibidas: {len(responses)} | ⏱️ Tiempo: {level_time}")

        if not isinstance(responses, list) or not responses:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid or missing responses'})
            }

        # 📦 Tablas DynamoDB
        question_table = dynamodb.Table(os.environ['TABLE_QUESTIONS'])
        session_table = dynamodb.Table(os.environ['TABLE_GAME_SESSIONS'])
        user_table = dynamodb.Table(os.environ['TABLE_USERS'])

        # 🔄 Llamada al Lambda getUserById para obtener classroom_id
        try:
            classroom_function_name = f"{os.environ['USER_SERVICE_NAME']}-{os.environ['STAGE']}-getUserById"
            token = event.get('headers', {}).get('Authorization')

            if not token:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Authorization token is missing'})
                }

            simulated_event = {
                "headers": {
                    "Authorization": token
                },
                "pathParameters": {
                    "user_id": user_id
                }
            }

            response = lambda_client.invoke(
                FunctionName=classroom_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(simulated_event)
            )

            user_response = json.loads(response['Payload'].read().decode())
            if 'statusCode' in user_response and user_response['statusCode'] != 200:
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Failed to retrieve user data', 'details': user_response})
                }

            user_body = json.loads(user_response.get('body', '{}'))
            classroom_id = user_body.get('classroom_id')

            if classroom_id:
                print(f"✅ classroom_id recibido: {classroom_id}")
            else:
                print("⚠️ classroom_id no encontrado en respuesta")

        except Exception as e:
            print(f"❌ Error llamando a getUserById: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal error while fetching classroom_id'})
            }

        if not classroom_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'classroom_id is missing from user data'})
            }

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

        # 💾 Guardar la sesión incluyendo classroom_id y level_time
        session_table.put_item(Item={
            'session_id': session_id,
            'user_id': user_id,
            'classroom_id': classroom_id,  # ✅ NUEVO
            'game_id': game_id,
            'level_number': level_number,
            'score': correct_count,
            'passed': passed,
            'results': results,
            'level_time': level_time,
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
            'levelTime': level_time,
            'classroom_id': classroom_id  # ✅ Opcional, lo devuelves si quieres
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