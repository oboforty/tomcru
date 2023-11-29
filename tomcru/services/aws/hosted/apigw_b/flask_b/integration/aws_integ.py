import json
import logging
from time import sleep

from botocore.auth import (
    SigV4Auth, SigV4QueryAuth,
    S3SigV4Auth, S3SigV4QueryAuth, S3SigV4PostAuth
)
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

logger = logging.getLogger('tomcru')


class RequestSigV4Auth(SigV4Auth):
    """
    Generates signature from an incoming request.
    The only difference vs SigV4Auth is that this uses the timestamp from the header and not datetime.now()
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _modify_request_before_signing(self, request: AWSRequest):
        # override timestamp before _modify_request_before_signing, as it later overrides the date header
        request.context['timestamp'] = request.headers['X-Amz-Date']

        return super(RequestSigV4Auth, self)._modify_request_before_signing(request)


class RequestSigV4AuthS3(S3SigV4Auth):
    """
    Generates signature from an incoming request.
    The only difference vs SigV4Auth is that this uses the timestamp from the header and not datetime.now()
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _modify_request_before_signing(self, request: AWSRequest):
        # override timestamp before _modify_request_before_signing, as it later overrides the date header
        request.context['timestamp'] = request.headers['X-Amz-Date']

        return super()._modify_request_before_signing(request)


def get_auth_claims(headers) -> dict:
    return dict(x.split('=') for x in headers['Authorization'].removeprefix('AWS4-HMAC-SHA256 ').split(', '))


def signv4_verify(request, *, secret_getter) -> tuple[str,str] | None:
    # todo: detect if it's not signv4 or if it's S3?
    # todo: add internal request class to pass flask.Request -> TomcruRequest -> AWSRequest

    # fetch request input:
    claims_request = get_auth_claims(request.headers)
    canonical_headers = {x: request.headers[x] for x in claims_request['SignedHeaders'].split(';')}
    key, _, region, serv_id, _ = claims_request['Credential'].split('/')

    # fetch user credentials:
    secret = secret_getter(key)
    creds = Credentials(key, secret)

    # generate sign from user credentials
    # "service_name" is generally "execute-api" for signing API Gateway requests
    aws_request = AWSRequest(method=request.method, url=request.url, data=request.data, params=None, headers=canonical_headers)

    if serv_id == 's3' and request.method == 'PUT':
        auth = RequestSigV4AuthS3(creds, serv_id, region)
    else:
        auth = RequestSigV4Auth(creds, serv_id, region)
    auth.add_auth(aws_request)

    # compare signature from user VS request
    claims_user = get_auth_claims(aws_request.headers)

    if claims_request['Signature'] != claims_user['Signature']:
        logger.error(f"[apigw] AWS Sigv4 invalid signature: \nExpected: {claims_user.get('Signature')}\nReceived: {claims_request.get('Signature')}")
        return None

    return serv_id, region


def aws_integ_parse_request(serv_id, region, request):
    target_args = {}
    target = None

    if request.headers.get('content_type') in ('application/json', 'application/x-amz-json-1.0'):
        target_args: dict = json.loads(request.data)

    # filter out integration details
    if 'X-Amz-Target' in request.headers:
        serv_internal_id, target = request.headers['X-Amz-Target'].split('.')

    return target, target_args


def on_request(srv, request, secret_getter):
    # pinku
    integ: tuple[str, str] = signv4_verify(request, secret_getter=secret_getter)

    if not integ:
        return {
            "__type": "com.amazon.coral.service#UnrecognizedClientException",
            "message": "The security token included in the request is invalid."
        }, 400

    target, target_args = aws_integ_parse_request(*integ, request)

    # todo: later: how to handle region parameter,
    #       that is not passed to `target` method, but only to parse_request?
    if hasattr(srv, 'aws_integ_parse_request'):
        target = srv.aws_integ_parse_request(target, integ[1], request, target_args)

    response = getattr(srv, target)(**target_args)

    if hasattr(srv, 'aws_integ_parse_response'):
        response = srv.aws_integ_parse_response(*integ, response)

    if isinstance(response, (dict, list)):
        return json.dumps(response, separators=(',', ":"))
    else:
        return response
