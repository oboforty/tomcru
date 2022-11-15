import requests

from .TomcruApiGWHttpIntegration import TomcruApiGWAuthorizerIntegration
from tomcru import TomcruApiOIDCAuthorizerDescriptor


class OIDCAuthorizerIntegration(TomcruApiGWAuthorizerIntegration):

    def __init__(self, cfg: TomcruApiOIDCAuthorizerDescriptor, auth_cfg, env=None):
        super().__init__(cfg)

        self.oidc_ep = cfg.endpoint_url
        self.env = env

    def authorize(self, event: dict):

        headers = {'Accept': 'application/json'}
        r = requests.get(self.oidc_ep, headers=headers)
        oidc = r.json()

        issuer = oidc['issuer']
        jwks_ep = oidc['jwks']

        r = requests.get(jwks_ep, headers=headers)
        jwks = r.json()

        # now verify JWT based on jwks



        # todo: JWT
        # todo: fetch kid from JWKS url
        # todo: sign JWT verify

        # todo: return

"""
# for https://server.com/.well-known/openid-configuration
{
  "issuer": "https://example.com/",
  "authorization_endpoint": "https://example.com/authorize",
  "token_endpoint": "https://example.com/token",
  "userinfo_endpoint": "https://example.com/userinfo",
  "jwks_uri": "https://example.com/.well-known/jwks.json",
  "scopes_supported": [
    "pets_read",
    "pets_write",
    "admin"
  ],
  "response_types_supported": [
    "code",
    "id_token",
    "token id_token"
  ],
  "token_endpoint_auth_methods_supported": [
    "client_secret_basic"
  ],
  ...
}
"""
