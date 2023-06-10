
CORS_ALL = 'all'


class FlaskCorsAfterRequestHook:
    def __init__(self, acl: dict):
        self.headers = {}
        self.allow = acl.get('allow', 'all')
        self.deny = acl.get('deny', [])

        if acl.get('use_defaults'):
            self.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, X-Requested-With, Content-Type, Authorization'
            self.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            self.headers['Access-Control-Allow-Credentials'] = 'true'
            self.headers['Access-Control-Max-Age'] = 86400

        self.headers.update(acl.get('headers', {}))

        if isinstance(self.deny, list): self.deny = set(self.deny)
        if isinstance(self.allow, list): self.allow = set(self.allow)
        if '*' == self.deny: self.deny = CORS_ALL
        if '*' == self.allow: self.allow = CORS_ALL

    def __call__(self, request, resp):

        resp.headers.update(self.headers)

        if "Access-Control-Allow-Origin" not in resp.headers:
            acl_allow_origin = None

            if not request.origin:
                if self.allow == CORS_ALL and self.deny != CORS_ALL:
                    acl_allow_origin = '*'
            else:
                if self.deny != CORS_ALL and request.origin not in self.deny:
                    if self.allow == CORS_ALL or request.origin in self.allow:
                        acl_allow_origin = request.origin

            # set headers
            if acl_allow_origin:
                resp.headers["Access-Control-Allow-Origin"] = acl_allow_origin

        return resp
