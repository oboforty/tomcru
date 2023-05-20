import logging

import requests
from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiOIDCAuthorizerEP


logger = logging.getLogger('tomcru')


class AWSOIDCException(Exception):
    pass


class OIDCAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):

    def __init__(self, cfg: TomcruApiOIDCAuthorizerEP, auth_cfg, env=None):
        super().__init__(cfg)
        self.env = env

        # OIDC config from swagger file (& envspec override):
        self.oidc_ep = auth_cfg.get(f'authorizers.{cfg.auth_id}.url_override', cfg.endpoint_url)
        self.audience = auth_cfg.get(f'authorizers.{cfg.auth_id}.audience')

        # remote OIDC endpoint information:
        self.initialized = False
        self.scopes_supported: list = None
        self.issuer = None
        self.jwks_client = None

    def authorize(self, event: dict):
        import jwt

        # initialize OIDC endpoint
        if not self.initialized:
            oidc_cfg = self._fetch_oidc_endpoint()
            self.jwks_client = jwt.PyJWKClient(oidc_cfg['jwks_uri'], cache_jwk_set=True, lifespan=900)

        if 'authorization' not in event['headers']:
            return None
        try:
            prefix, token_jwt = event['headers']['authorization'].split(" ")
            assert prefix.lower() in ('bearer', 'jwt')

            # base64 decode JWT & get JWK for it
            signing_key = self.jwks_client.get_signing_key_from_jwt(token_jwt)

            # verify JWT
            data = jwt.decode(token_jwt, signing_key.key, algorithms=["RS256"], audience=self.audience, issuer=self.issuer)
            #headers = jwt.get_unverified_header(token_jwt)
            # jwk = next(filter(lambda x: x['kid'] == kid, jwks))

            scopes = self.verify_claims(data)

            if data:
                # integrate into event
                event['requestContext']['authorizer'] = {
                    'jwt': {
                        'claims': data,
                        'scopes': scopes
                    }
                }

            return data
        except (jwt.InvalidTokenError, AWSOIDCException) as e:
            # invalidated claims -> authorizer refuses the token

            logger.error("[OIDC] JWT Authorizer error: ", str(type(e)), e)
            return None

    def verify_claims(self, data: dict):
        _scope = data.get('scp', data.get('scope', None))

        # validate: The token must include at least one of the scopes in the route's authorizationScopes
        #self.scope, self.scopes_supported

        if self.scopes_supported:
            if not _scope:
                raise AWSOIDCException("no scope provided in JWT")
            elif _scope not in self.scopes_supported:
                raise AWSOIDCException("scope validation error")

        return _scope

    def _fetch_oidc_endpoint(self):
        headers = {'Accept': 'application/json'}
        try:
            r = requests.get(self.oidc_ep, headers=headers)
        except requests.exceptions.ConnectionError:
            raise AWSOIDCException()

        if r.status_code != 200:
            raise AWSOIDCException()
        oidc = r.json()

        self.issuer = oidc['issuer']
        self.scopes_supported = oidc['scopes_supported']

        return oidc
