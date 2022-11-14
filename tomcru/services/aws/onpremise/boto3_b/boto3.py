
class Boto3:
    __TOMCRU__ = True

    def __init__(self, objs):
        self._objs = objs

    def client(self, resname, **kwargs):
        assert resname in ('s3', 'dynamodb', 'ses', 'apigatewaymanagementapi')
        return self._objs.get('boto3', resname).boto3(**kwargs)

    def resource(self, resname, **kwargs):
        assert resname in ('s3', 'dynamodb')
        return self._objs.get('boto3', resname).boto3(**kwargs)

    def Session(self):
        return self
