from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiLambdaAuthorizerDescriptor


class LambdaAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):

    def __init__(self, cfg: TomcruApiLambdaAuthorizerDescriptor, auth_cfg, lambda_builder, env=None):
        super().__init__(cfg)

        self.lambda_builder = lambda_builder

        self.lambda_folder = cfg.lambda_source
        self.lambda_id = cfg.lambda_id
        self.env = env

        self.lambda_builder.build_lambda(self.lambda_id, env=self.env)

    def authorize(self, event: dict, source='headers'):
        """
        Runs lambda

        :param event: api gw integration events
        :param source: provided source of authorization token (headers | params | body)

        :return: if authorized
        """
        auth_event = {
            'queryStringParameters': event.get('queryStringParameters', {}).copy(),
            "methodArn": event['methodArn'],
            'requestContext': event['requestContext'].copy(),
            'headers': event.get('headers', {}).copy()
        }

        if 'headers' == source:
            auth_event['identitySource'] = auth_event['headers'].get('authorization')
        elif 'params' == source:
            auth_event['identitySource'] = auth_event['queryStringParameters'].get('authorization')

        # check if cached
        cache_key = auth_event['identitySource']
        user = self.get_cache(cache_key)

        if not user:
            resp = self.lambda_builder.run_lambda(self.lambda_id, auth_event, self.env)

            if self.parse_auth_response(resp):
                user = resp['context']
            else:
                user = None
                # todo: don't let pass through? check aws docks
            if user:
                # cache authorizer response
                self.authorizers_cache[cache_key] = user

        if user:
            # integrate into event
            event['requestContext']['authorizer'] = {
                'lambda': user.copy()
            }

        return user

    def parse_auth_response(self, resp):
        if 'statusCode' in resp or 'isAuthorized' in resp:
            # simplified authorizer:
            return resp.get('statusCode', 200) == 200 and resp.get('isAuthorized')
        elif 'policyDocument' in resp:
            # IAM policy
            return resp['policyDocument'].get('Statement', [{}])[0].get('Effect') == 'Allow'
