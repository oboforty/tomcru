import os.path
import json
from io import StringIO

from core.utils.yaml_custom import yaml

def handler(event, context):
    api_name = event['queryStringParameters']['api_name']

    content_header = event['headers']['content-type']
    req_content = event['queryStringParameters']['content']
    out_content = 'yaml' if os.path.exists(api_name+'.yaml') else 'json'

    fn = api_name+'.'+req_content

    try:
        if req_content == out_content:
            with open(fn) as fh:
                return {
                    "statusCode": 200,
                    "body": fh.read(),
                    "headers": {
                        "content-type": f"application/{out_content}"
                    }
                }
        elif req_content == 'json' and out_content == 'yaml':
            with open(fn) as fh:
                configuration = yaml.safe_load(fh)

            return {
                "statusCode": 200,
                "body": json.dumps(configuration),
                "headers": {
                    "content-type": f"application/{out_content}"
                }
            }
        elif req_content == 'yaml' and out_content == 'json':
            buf = StringIO()

            with open(fn) as fh:
                swagger_json = json.load(fh)

            yaml.dump(swagger_json, buf, allow_unicode=True)

            return {
                "statusCode": 200,
                "body": buf.getvalue(),
                "headers": {
                    "content-type": f"application/{out_content}"
                }
            }
    except Exception as e:
        raise e

        return {
            "statusCode": 500,
            "body": "{}"
        }
