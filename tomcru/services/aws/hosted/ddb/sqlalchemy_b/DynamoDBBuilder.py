from .DdbSqlalchemyAdapter import DdbSqlAlchemyAdapter
from .dal_ddb import build_database
from tomcru.services.ServiceBase import ServiceBase


class DynamoDBBuilder(ServiceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ddb = None

    def init(self):
        if self.ddb:
            raise Exception("Already initialized")

        sess, tables = build_database(self.env.app_path, self.opts.get('conn.dsn'), self.cfg.conf.get('tables'))

        # todo: later: group obj instances by AWS-REGION
        self.ddb = DdbSqlAlchemyAdapter(sess, tables)

        self.service('boto3').add_resource('dynamodb', self)

    def as_boto3_resource(self, **kwargs):
        """
        Returns wrapper object for boto3 onpremise mock library
        :param kwargs: DDB resource/client extra args
        :return: boto3 resource for DDB
        """
        return self.ddb
