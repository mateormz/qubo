import json
import os
import boto3

def validate_token(event, lambda_client):
    try:
        user_table_name = os.environ['TABLE_USERS']
        validate_function_name = f"{os.environ['SERVICE_NAME']}-{os.environ['STAGE']}-{os.environ['VALIDATE_TOKEN_FUNCTION']}"
        print("[INFO] Environment variables loaded successfully")
    except KeyError as env_error:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f"Missing environment variable: {str(env_error)}"})
        }

    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }

    token = body.get('token')

    if not token:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Authorization token is missing'})
        }

    payload = {"body": json.dumps({"token": token})}
    validate_response = lambda_client.invoke(
        FunctionName=validate_function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    validation_result = json.loads(validate_response['Payload'].read())

    if validation_result.get('statusCode') != 200:
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Unauthorized - Invalid or expired token'})
        }

    try:
        user_info = json.loads(validation_result.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error - Invalid token response format'})
        }

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