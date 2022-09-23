from .DdbSqlalchemyAdapter import DdbSqlAlchemyAdapter
from ..dal_ddb import build_database


class Boto3:
    __TOMCRU__ = True

    def __init__(self, app, app_path):
        # build DDB adapter -- @todo: replace with test MOCK ?
        sess, tables = build_database(app_path)
        self.ddb = DdbSqlAlchemyAdapter(sess, tables)
        self.apigw = app

    def client(self, resname, **kwargs):
        if 's3' == resname:
            pass
        elif 'ses' == resname:
            pass
        elif 'apigatewaymanagementapi' == resname:
            # todo: @later: handle app apis and not fake endpoint url!
            self.apigw.endpoint_url = kwargs.get('endpoint_url')
            return self.apigw
        elif 's3' == resname:
            pass

    def resource(self, resname):
        if 's3' == resname:
            pass
        elif 'dynamodb' == resname:
            return self.ddb

    def Session(self):
        return self

