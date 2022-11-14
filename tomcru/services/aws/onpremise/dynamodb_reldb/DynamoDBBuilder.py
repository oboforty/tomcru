from .DdbSqlalchemyAdapter import DdbSqlAlchemyAdapter
from .dal_ddb import build_database
from tomcru import TomcruProject


class DynamoDBBuilder:
    def __init__(self, project: TomcruProject, opts):
        """
        Stores AWS service objects to be accessible both internally in a tomcru app and externally (e.g. tomcru used as a library)
        :param project:
        :param opts:
        """
        self.cfg = project.cfg
        self.opts = opts
        self.objs = project.serv('aws:onpremise:obj_store')

        self.ddb = None

    def init(self):
        if self.ddb:
            raise Exception("Already initialized")

        sess, tables = build_database(self.cfg.app_path, self.opts.conf.copy())

        # todo: later: group obj instances by AWS-REGION
        self.ddb = DdbSqlAlchemyAdapter(sess, tables)

        self.objs.add('boto3', 'dynamodb', self)

    def boto3(self, **kwargs):
        """
        Returns wrapper object for boto3 onpremise mock library
        :param kwargs: DDB resource/client extra args
        :return: boto3 resource for DDB
        """
        return self.ddb
