import jwt

import requests

from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiOIDCAuthorizerDescriptor

class AWSOIDCException(Exception):
    pass


class OIDCAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):

    def __init__(self, cfg: TomcruApiOIDCAuthorizerDescriptor, auth_cfg, env=None):
        super().__init__(cfg)
        self.env = env

        self.oidc_ep = cfg.endpoint_url
        self.audience = cfg.audience
        self.scopes = cfg.scopes # this is redundant (scopes_supported is fetched from OIDC ep); but AWS requires to be checked

        # OIDC endpoint:
        self.initialized = False
        self.scopes_supported: list = None
        self.issuer = None
        self.jwks_client: jwt.PyJWKClient | None = None

    def authorize(self, event: dict):
        self._initialize_oidc()

        if 'authorization' not in event['headers']:
            return None
        token_jwt: str = event['headers']['authorization'].removeprefix('Bearer ')

        try:
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
            print("Auth error: ", e)
            return None

    def verify_claims(self, data: dict):
        # TODO: ITT: what other stuff we need to check that JWT lib doesn't?
        _scope = data.get('scp', data.get('scope', None))

        if self.scopes:
            if not _scope:
                raise AWSOIDCException("no scope provided in JWT")
            elif _scope not in self.scopes:
                raise AWSOIDCException("scope validation error")

        return _scope

    def _initialize_oidc(self):
        if self.initialized:
            return False

        # fetch OIDC endpoint and find JWKS
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
        # validate: The token must include at least one of the scopes in the route's authorizationScopes
        #self.scope, self.scopes_supported

        self.jwks_client = jwt.PyJWKClient(oidc['jwks_uri'], cache_jwk_set=True, lifespan=900)

        return True
