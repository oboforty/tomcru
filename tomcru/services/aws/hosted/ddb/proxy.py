import sys
import json
from base64 import b64decode, b64encode
from contextlib import contextmanager


def t_out(output):
    resp = b64encode(json.dumps(output).encode('utf8')).decode('utf8')
    sys.stdout.write(resp)


def execute(t_in):
    serv_id = t_in['serv_id']
    CALL_BOTO = t_in.get('boto3', None)

    if CALL_BOTO:
        import boto3

        if CALL_BOTO == 'resource':
            serv = boto3.resource(serv_id)

            resource_type = t_in.get('resource_type')
            resource_id = t_in.get('resource_id')

            if resource_type:
                serv = getattr(serv, resource_type)(resource_id)
        else:
            serv = boto3.client(serv_id)
    else:
        raise NotImplementedError("Non-boto service call!")

    resp = getattr(serv, t_in['method'])(**t_in['args'])

    t_out(resp)


@contextmanager
def node_boto3_proxy():
    input_b64 = sys.stdin.read()
    t_in = json.loads(b64decode(input_b64.encode('utf8')))

    yield (t_in, execute)
