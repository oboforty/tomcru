

class WsEnRouteCachedAuthorizer:

    def __init__(self, apigw_authorizer):
        self.auth = apigw_authorizer
        self.connect_authorization_success = False

    def authorize(self, *args, **kwargs):
        if self.auth is None:
            return True
        self.connect_authorization_success = self.auth.authorize(*args, **kwargs)

        return self.connect_authorization_success

    def check_cached_auth(self, event):
        if self.auth is None:
            return True

        user = self.connect_authorization_success

        if user:
            event['requestContext']['authorizer'] = {
                'lambda': user.copy()
            }

        return user