import json
import os

def validate_token(event, lambda_client):
    try:
        validate_function_name = f"{os.environ['USER_SERVICE_NAME']}-{os.environ['STAGE']}-{os.environ['VALIDATE_TOKEN_FUNCTION']}"
    except KeyError as env_error:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'}, #axaaz
            'body': json.dumps({'error': f"Missing environment variable: {str(env_error)}"})
        }

    token = event.get('headers', {}).get('Authorization')
    if not token:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Authorization token is missing'})
        }

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
            'body': json.dumps({'error': 'Unauthorized'})
        }

    return json.loads(validation_result.get('body', '{}'))

def ensure_teacher(user_info):
    if user_info.get('role') != 'teacher':
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Only teachers can use this feature'})
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
