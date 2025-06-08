import json
import os
import boto3

lambda_client = boto3.client('lambda')

def validate_token(event, lambda_client=lambda_client):
    try:
        validate_function_name = f"{os.environ['USER_SERVICE_NAME']}-{os.environ['STAGE']}-{os.environ['VALIDATE_TOKEN_FUNCTION']}"
    except KeyError as env_error:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f"Missing environment variable: {str(env_error)}"})
        }

    # Obtener token desde el header Authorization
    token = event.get('headers', {}).get('Authorization')
    if not token:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Authorization token is missing'})
        }

    # Construir payload para invocar Lambda externa
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

    # Asegurarse que el body exista y convertirlo
    body_str = validation_result.get('body')
    if body_str is None:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Token validation response missing body'})
        }

    user_info = json.loads(body_str)
    return user_info
