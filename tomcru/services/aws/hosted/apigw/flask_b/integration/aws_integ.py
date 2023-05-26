import json
import logging
from time import sleep

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

logger = logging.getLogger('tomcru')


class SigV4AuthFromRequest(SigV4Auth):
    """
    Generates signature from an incoming request.
    The only difference vs SigV4Auth is that this uses the timestamp from the header and not datetime.now()
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _modify_request_before_signing(self, request: AWSRequest):
        # override timestamp before _modify_request_before_signing, as it later overrides the date header
        request.context['timestamp'] = x_amz_date = request.headers['X-Amz-Date']

        return super(SigV4AuthFromRequest, self)._modify_request_before_signing(request)


def get_auth_claims(headers) -> dict:
    return dict(x.split('=') for x in headers['Authorization'].removeprefix('AWS4-HMAC-SHA256 ').split(', '))


def signv4_verify(request, *, secret_getter) -> dict | None:
    # todo: detect if it's not signv4 or if it's S3?
    # todo: add internal request class to pass flask.Request -> TomcruRequest -> AWSRequest

    # fetch request input:
    claims_request = get_auth_claims(request.headers)
    canonical_headers = {x: request.headers[x] for x in claims_request['SignedHeaders'].split(';')}
    key, _, region, serv_id, _ = claims_request['Credential'].split('/')

    # fetch user credentials:
    token = None
    secret = secret_getter(key)
    creds = Credentials(key, secret, token)

    # generate sign from user credentials
    # "service_name" is generally "execute-api" for signing API Gateway requests
    aws_request = AWSRequest(method=request.method, url=request.url, data=request.data, params=None, headers=canonical_headers)

    auth = SigV4AuthFromRequest(creds, serv_id, region)
    auth.add_auth(aws_request)

    # compare signature from user VS request
    claims_user = get_auth_claims(aws_request.headers)

    if claims_request['Signature'] != claims_user['Signature']:
        return None

    # filter out all integration details
    serv_internal_id, target = request.headers['X-Amz-Target'].split('.')
    integ_details = dict(
        region=region, serv_id=serv_id, serv_internal_id=serv_internal_id, target=target,
        content_type=canonical_headers['content-type'],
        #key=key, user=None
    )

    return integ_details


def on_request(srv, request, secret_getter):
    # pinku
    integ = signv4_verify(request, secret_getter=secret_getter)

    if not integ:
        return "invalid_signature", 403

    # auto convert
    target_args: dict | None = None
    if integ['content_type'] in ('application/json', 'application/x-amz-json-1.0'):
        target_args: dict = json.loads(request.data)

    if not target_args:
        raise NotImplementedError("WTF?")

    # service decides how to convert
    if hasattr(srv, 'aws_integ_parse_request'):
        target_args: dict = srv.aws_integ_parse_request(integ, target_args)

    response = getattr(srv, integ['target'])(**target_args)

    if not isinstance(response, (str, dict, list)):
        logger.error(f"Non-JSON format received by hosted AWS service: {srv.__class__.__name__}")
        raise Exception("Non-JSON response returned: " + str(type(response)))

    if hasattr(srv, 'aws_integ_parse_response'):
        response = srv.aws_integ_parse_response(integ, response)

    if isinstance(response, (dict, list)):
        return json.dumps(response, separators=(',', ":"))
    else:
        return response
