from tomcru import TomcruSubProjectCfg, TomcruEnvCfg, TomcruApiAuthorizerDescriptor, TomcruApiLambdaAuthorizerDescriptor


def build_authorizers(authorizers: dict[str, TomcruApiAuthorizerDescriptor], env: TomcruEnvCfg):
    self.authorizers: Dict[str, TomcruApiGWAuthorizerIntegration] = {}

    # build authorizers
    for authorizer_id, auth in authorizers.items():
        if isinstance(auth, TomcruApiLambdaAuthorizerDescriptor):
            # evaluate lambda sub type
            if 'external' == auth.lambda_source:
                self.authorizers[authorizer_id] = ExternalLambdaAuthorizerIntegration(auth,
                                                                                      self.apigw_cfg)
            else:
                self.authorizers[authorizer_id] = LambdaAuthorizerIntegration(auth, self.apigw_cfg,
                                                                              self.p.serv(
                                                                                  'aws:onpremise:lambda_b'),
                                                                              env=self.env)

        elif isinstance(auth, TomcruApiOIDCAuthorizerDescriptor):
            self.authorizers[authorizer_id] = OIDCAuthorizerIntegration(auth, self.apigw_cfg,
                                                                        env=self.env)
        else:
            # todo: implement IAM and jwt
            raise NotImplementedError(authorizer_id)

    return self.authorizers
