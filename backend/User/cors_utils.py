import json

def respond(status_code, payload):
    """
    Genera una respuesta HTTP con los headers de CORS ya incluidos.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
        },
        "body": json.dumps(payload)
    }

def cors_handler(func):
    """
    Decorator para envolver handlers de Lambda y agregar CORS automáticamente.
    """
    def wrapper(event, context):
        # Respuesta preflight
        if event.get("httpMethod") == "OPTIONS":
            return respond(200, {})

        # Llamada al handler real
        result = func(event, context)

        # Inyecta headers CORS si el handler devolvió un dict
        if isinstance(result, dict):
            headers = result.get("headers", {})
            headers.update({
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
            })
            result["headers"] = headers
        return result

    return wrapper