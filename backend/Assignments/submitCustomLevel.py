import json
import os
import boto3
import uuid
from datetime import datetime
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')  # Crear el cliente de Lambda

def lambda_handler(event, context):
    try:
        # Validar token
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        user_id = user_info['user_id']
        level_id = event['pathParameters'].get('level_id')
        body = json.loads(event.get('body', '{}'))
        responses = body.get('responses', [])
        level_time = body.get('level_time', '')  # ⬅️ Nuevo campo

        if not isinstance(responses, list) or not responses:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid or missing responses'})}

        # Recuperar nivel
        levels = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        lvl = levels.get_item(Key={'level_id': level_id})
        if 'Item' not in lvl:
            return {'statusCode': 404, 'body': json.dumps({'error': f'Custom level {level_id} not found'})}

        qids = lvl['Item'].get('questions_ids', [])
        qt = dynamodb.Table(os.environ['TABLE_CUSTOM_QUESTIONS'])
        correct = 0
        results = []

        for resp in responses:
            qid = resp.get('question_id')
            sel = resp.get('selectedIndex')
            if qid not in qids:
                continue
            item = qt.get_item(Key={'question_id': qid}).get('Item')
            if not item:
                continue
            is_corr = sel == item['correctIndex']
            if is_corr:
                correct += 1
            results.append({
                'question_id': qid,
                'was_correct': is_corr,
                'topic': item.get('topic', 'N/A'),
                'text': item.get('text'),
                'options': item.get('options'),
                'selected_index': sel
            })

        # 🔄 Llamada al Lambda getUserById (simulando request API Gateway)
        try:
            classroom_function_name = f"{os.environ['USER_SERVICE_NAME']}-{os.environ['STAGE']}-getUserById"
            token = event.get('headers', {}).get('Authorization')

            if not token:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Authorization token is missing'})
                }

            # Simular event como lo enviaría API Gateway
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

        passed = correct >= 6
        session_id = str(uuid.uuid4())

        sess = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        sess.put_item(Item={
            'session_id': session_id,
            'user_id': user_id,
            'classroom_id': classroom_id,
            'level_id': level_id,
            'score': correct,
            'passed': passed,
            'results': results,
            'timestamp': datetime.utcnow().isoformat(),
            'level_time': level_time  # ⬅️ Guardado en sesión
        })

        levels.update_item(
            Key={'level_id': level_id},
            UpdateExpression="SET submissions = list_append(submissions, :s)",
            ExpressionAttributeValues={':s': [{
                'user_id': user_id,
                'score': correct,
                'passed': passed,
                'submission_id': session_id,
                'classroom_id': classroom_id,
                'level_time': level_time  # ⬅️ También guardado en el nivel
            }]}
        )

        return {
            'statusCode': 200,
            'body': json.dumps(convert_decimal({
                'sessionId': session_id,
                'score': correct,
                'passed': passed,
                'incorrectQuestions': [r for r in results if not r['was_correct']]
            }))
        }

    except Exception as e:
        print(f"❌ Error general en submit: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error', 'details': str(e)})}
