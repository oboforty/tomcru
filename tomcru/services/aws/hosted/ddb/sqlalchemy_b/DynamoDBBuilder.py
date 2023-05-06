from .boto3_proxy import DDBResource
from .dal_ddb import build_database
from tomcru.services.ServiceBase import ServiceBase

from .DDBSqlAlchemyTable import DDBSqlAlchemyTable
from .boto3_proxy import DDBClient, DDBResource


class DynamoDBBuilder(ServiceBase):
    INIT_PRIORITY = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cli = None
        self.res = None

    def init(self):
        if self.cli:
            raise Exception("DDB: Already initialized")

        # todo: later: group obj instances by AWS-REGION ?
        sess, tables = build_database(self.env.app_path, self.opts.get('conn.dsn'), self.cfg.conf.get('tables'))
        tables = {k: DDBSqlAlchemyTable(sess, *t) for k,t in tables.items()}
        self.cli = DDBClient(tables)
        self.res = DDBResource(tables)

        self.service('boto3').add_resource('dynamodb', self.res)
        self.service('boto3').add_client('dynamodb', self.cli)
