
    def get_event_and_context(self):


        self.load_user(event, groupHandler.lambda_builder)

        # fake aws event & ctx
        _lam_arsg = []
        _lam_arsg.append(event)
        if len(sig.parameters) >= 2:
            _lam_arsg.append(groupHandler.lambda_builder.get_context())

        return lamb, lamb_fn, _lam_arsg


    def mock_authorizer(self, response):
        # hack for eme comma parser:
        if isinstance(response, list):
            response = ','.join(response)

        user = json.loads(response) if isinstance(response, str) else response

        authorizer_fn = lambda event, ctx: {
            "principalId": "me",
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow" if 'queryStringParameters' in event and 'authorization' in event['queryStringParameters'] else 'Deny',
                    "Resource": event['methodArn']
                }
            ],
            "context": user,
        }

        self.authorizer = '__MOCK__', authorizer_fn
