import logging
import os.path

from tomcru.services.ServiceBase import ServiceBase

__dir__ = os.path.dirname(os.path.realpath(__file__))


logger = logging.getLogger('tomcru')


class LambdaBuilder(ServiceBase):
    INIT_PRIORITY = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inject_dependencies(self):
        pass

    def init(self):
        # TODO: ITT:
        #       - 1 example lambda
        #       - copy deploy code/cfg needed from ops
        #       - test deploy
        #       - impl tomcru lambda, apigw, ddb, s3, sqs
        app = self.service('cdk_app')

        lambda_ = app.cdk.aws_lambda

        lamb = lambda_.Function(
            #app.stack,
            app.stacks['base'],
            f"mierda-lambda",
            function_name=f"mierda-indexer",
            handler="app.lambda_handler",
            architecture=lambda_.Architecture.ARM_64,
            runtime=lambda_.Runtime.PYTHON_3_12,
            # memory_size=2048,
            # reserved_concurrent_executions=5,
            # ephemeral_storage_size=Size.mebibytes(512),
            # timeout=Duration.minutes(15),
            code=lambda_.Code.from_asset("cloudapp_est/lambdas/services/VersionIndex"),
            #timeout=Duration.minutes(15),
            environment={
                "hetyetye": "true",
            },
        )

