import os
import json


def handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps([
            {
                "id": 1,
                "name": "Dr Oetker",
                "tag": "moa"
            },
            {
                "id": 2,
                "name": "Tesomsz",
                "tag": "ali"
            }
        ]),
        "headers": {
            "x-next": "yoyoyo"
        }
    }
