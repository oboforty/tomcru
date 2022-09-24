import json
import uuid


def handle_lambda_request(event: dict) -> dict:
    try:
        user = event['requestContext']['authorizer']['lambda']
    except Exception as e:
        user = None

    _body = event.get('body')
    event = event.get('queryStringParameters', event)

    if _body:
        # parse json body
        event.update(json.loads(_body))

    # if not user:
    #     return None
    # elif not isinstance(user, dict):
    #     user = json.loads(user)

    return event, user

def get_id():
    return str(uuid.uuid4())
