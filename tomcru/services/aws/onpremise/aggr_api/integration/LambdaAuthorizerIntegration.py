from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiLambdaAuthorizerDescriptor


class LambdaAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):

    def __init__(self, cfg: TomcruApiLambdaAuthorizerDescriptor, auth_cfg, lambda_builder, env=None):
        super().__init__(cfg)

        self.lambda_builder = lambda_builder

        self.lambda_folder = cfg.lambda_source
        self.lambda_id = cfg.lambda_id
        self.env = env

        self.source = cfg.src_in
        self.source_name = cfg.src_name

        if self.source is None:
            self.source = 'headers'
        elif self.source == 'query':
            self.source = 'queryStringParameters'
        else:
            self.source += 's'

        if self.source == 'cookies':
            raise NotImplementedError("Cookies are not yet supported in tomcru authorization (in local FaaS)")

        self.lambda_builder.build_lambda(self.lambda_id, env=self.env)

    def authorize(self, event: dict):
        """
        Runs lambda

        :param event: api gw integration events
        :param source: provided source of authorization token (headers | params | body)

        :return: if authorized
        """

        auth_event = {
            "methodArn": event.get('methodArn', None),
            'requestContext': event['requestContext'].copy(),

            'queryStringParameters': event.get('queryStringParameters', {}).copy(),
            'headers': event.get('headers', {}).copy(),
        }
        auth_event['identitySource'] = auth_event[self.source].get(self.source_name)

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

