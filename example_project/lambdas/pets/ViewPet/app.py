import os


def handler(event, context):
    petId = event['queryStringParameters']['petId']

    return {
        "id": petId,
        "name": "Tesomsz",
        "tag": "ali",
        "hp": 100
    }
