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
        
        if not isinstance(responses, list) or not responses:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid or missing responses'})}

        # Recuperar nivel
        levels = dynamodb.Table(os.environ['TABLE_CUSTOM_LEVELS'])
        lvl = levels.get_item(Key={'level_id': level_id})
        if 'Item' not in lvl:
            return {'statusCode': 404, 'body': json.dumps({'error': f'Custom level {level_id} not found'})}

        qids = lvl['Item'].get('questions_ids', [])
        # Verificar respuestas contra custom-questions
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
            if is_corr: correct += 1
            results.append({
                'question_id': qid,
                'was_correct': is_corr,
                'topic': item.get('topic', 'N/A'),
                'text': item.get('text'),
                'options': item.get('options'),
                'selected_index': sel
            })

        # Llamada interna al Lambda para obtener el classroom_id, pasando también el token
        try:
            classroom_function_name = f"{os.environ['USER_SERVICE_NAME']}-{os.environ['STAGE']}-getUserById"  # Correcto formato
            token = event.get('headers', {}).get('Authorization')  # Obtener el token desde los headers

            # Verificar si se obtuvo el token
            if not token:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Authorization token is missing'})
                }

            response = lambda_client.invoke(
                FunctionName=classroom_function_name,  # Usamos el nombre correcto de la función Lambda
                InvocationType='RequestResponse',  # Síncrona
                Payload=json.dumps({'user_id': user_id, 'token': token})  # Pasamos el user_id y el token
            )
            user_data = json.loads(response['Payload'].read().decode())
            classroom_id = user_data.get('classroom_id')  # Extraemos el classroom_id

            # Log para verificar si classroom_id se obtuvo correctamente
            if classroom_id:
                print(f"Successfully retrieved classroom_id: {classroom_id}")
            else:
                print("No classroom_id found for the given user_id")

        except Exception as e:
            print(f"Error calling Lambda for classroom_id: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal error while fetching classroom_id'})
            }

        # Si no se obtiene classroom_id, devolver un error
        if not classroom_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'classroom_id is missing from user data'})
            }

        passed = correct >= 6
        session_id = str(uuid.uuid4())

        # Guardar sesión con classroom_id
        sess = dynamodb.Table(os.environ['TABLE_SESSIONS'])
        sess.put_item(Item={
            'session_id': session_id,
            'user_id': user_id,
            'classroom_id': classroom_id,  # Guardamos el classroom_id
            'level_id': level_id,
            'score': correct,
            'passed': passed,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Actualizar submissions en el nivel
        levels.update_item(
            Key={'level_id': level_id},
            UpdateExpression="SET submissions = list_append(submissions, :s)",
            ExpressionAttributeValues={':s': [{
                'user_id': user_id,
                'score': correct,
                'passed': passed,
                'submission_id': session_id,
                'classroom_id': classroom_id  # Añadir classroom_id a las submissions
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
        print(f"Error occurred: {str(e)}")  # Agregar log de error
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error', 'details': str(e)})}
