import json
import os
import boto3
from collections import defaultdict
from common import validate_token, convert_decimal

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    try:
        user_info = validate_token(event, lambda_client)
        if 'statusCode' in user_info:
            return user_info

        games_table = dynamodb.Table(os.environ['TABLE_GAMES'])
        levels_table = dynamodb.Table(os.environ['TABLE_LEVELS'])

        # Obtener todos los juegos
        games_response = games_table.scan()
        games = convert_decimal(games_response.get('Items', []))

        # Obtener todos los niveles
        levels_response = levels_table.scan()
        levels = convert_decimal(levels_response.get('Items', []))

        # Contar niveles por game_id
        level_counts = defaultdict(int)
        for level in levels:
            game_id = level.get('game_id')
            if game_id:
                level_counts[game_id] += 1

        # Asignar level_count a cada juego
        for game in games:
            game_id = game.get('game_id')
            game['level_count'] = level_counts.get(game_id, 0)

        return {
            'statusCode': 200,
            'body': json.dumps({'games': games})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
