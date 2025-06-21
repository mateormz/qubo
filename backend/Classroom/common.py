import json
import os
import boto3

def validate_token(event, lambda_client):
    try:
        validate_function_name = f"{os.environ['USER_SERVICE_NAME']}-{os.environ['STAGE']}-{os.environ['VALIDATE_TOKEN_FUNCTION']}"
    except KeyError as env_error:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f"Missing environment variable: {str(env_error)}"})
        }

    # Obtener token desde header Authorization
    token = event.get('headers', {}).get('Authorization')
    if not token:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Authorization token is missing'})
        }

    # Construir payload para la función de validación
    payload = {
        "body": json.dumps({"token": token})
    }

    try:
        validate_response = lambda_client.invoke(
            FunctionName=validate_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        validation_result = json.loads(validate_response['Payload'].read())
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f"Error invoking token validator: {str(e)}"})
        }

    if validation_result.get('statusCode') != 200:
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Unauthorized - Invalid or expired token'})
        }

    # Asegurarse de que el body exista
    body_str = validation_result.get('body')
    if body_str is None:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Token validation response missing body'})
        }

    user_info = json.loads(body_str)
    return user_info


def ensure_teacher(user_info):
    if user_info.get('role') != 'teacher':
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Unauthorized - Only teachers can perform this action'})
        }
    return None


def ensure_user_ownership(event, authenticated_user_id):
    try:
        path_user_id = event['pathParameters']['user_id']
    except KeyError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing path parameter: user_id'})
        }

    if path_user_id != authenticated_user_id:
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Unauthorized - You can only access your own account'})
        }

    return None

def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj