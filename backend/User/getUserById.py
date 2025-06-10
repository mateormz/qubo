import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from common import validate_token, ensure_user_ownership, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        error = ensure_user_ownership(event, user_info['user_id'])
        if error:
            return error

        user_table = dynamodb.Table(os.environ['TABLE_USERS'])
        games_table = dynamodb.Table(os.environ['TABLE_GAMES'])

        user_id = event['pathParameters']['user_id']

        response = user_table.get_item(Key={'user_id': user_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'User not found'})
            }

        item.pop('password_hash', None)

        level_progress = item.get('levelProgress', {})
        updated = False

        # Obtener todos los game_id existentes
        all_games = games_table.scan().get('Items', [])
        for game in all_games:
            game_id = game['game_id']
            if game_id not in level_progress:
                level_progress[game_id] = 1
                updated = True

        if updated:
            item['levelProgress'] = level_progress
            user_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='SET levelProgress = :lp',
                ExpressionAttributeValues={':lp': level_progress}
            )

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(convert_decimal(item))
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal Server Error', 'details': str(e)})
        }
