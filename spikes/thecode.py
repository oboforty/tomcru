import json

import json


def edes_faszom(event: dict, context = None):
    # tesomsz
    p: str = event['requestContext']['protocol']
    qu: int = event['queryStringParams']['gec']
    fostos = json.loads(event['body'])

    te = fostos['gec']

    #szarfaszu = [p, qu]

    print(event)
    print(5)

    #sys.exit()

    return {
        "event": dict(event),
        "kek": {
           "szar": fostos['cecelegy']['szarcsi']
        },
        "gecimre": int(event['queryStringParams']['tesomsz'])
    }
