from tomcru import TomcruApiOIDCAuthorizerDescriptor


class SAMOIDCAuthBuilder:
    def __init__(self, param_builder):
        self.param_builder = param_builder

    def build(self, auth_id, auth: TomcruApiOIDCAuthorizerDescriptor, apiopts):
        auth_integ = {
            'type': 'jwt',
            # Authorization header is staticly set for OIDC
            'identitySource': "$request.header.Authorization",
            'jwtConfiguration': {},
            'openIdConnectUrl': auth.endpoint_url
        }

        issuer = None

        if issuer: auth_integ['jwtConfiguration']['issuer'] = issuer
        if auth.audience: auth_integ['jwtConfiguration']['audience'] = auth.audience
        if auth.scopes: auth_integ['AuthorizationScopes'] = auth.scopes

        return auth_integ
