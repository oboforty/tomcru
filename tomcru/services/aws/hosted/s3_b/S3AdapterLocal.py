import logging
import os.path
import shutil

from deepmerge import always_merger
from flask import send_from_directory
from typing.io import BinaryIO

logger = logging.getLogger('tomcru')


class S3AdapterLocal:

    def __init__(self, app_path, cfg, opts):
        """
        Boto3 resource adapter for S3
        """
        _default_bucket_path = opts.get('path')
        self.buckets = always_merger.merge(cfg.get('buckets'), opts.get('buckets'))

        for bucket, bucket_cfg in self.buckets.items():
            path = bucket_cfg.get('path', os.path.join(_default_bucket_path, bucket))
            bucket_cfg['path'] = os.path.join(app_path, path)

            if not os.path.exists(bucket_cfg['path']):
                logger.debug(f"S3AdapterLocal: creating bucket directory: {bucket_cfg['path']}")
                os.makedirs(bucket_cfg['path'])

    def aws_integ_parse_request(self, target, region, request, target_args):
        if target is None:
            target = f'{request.method.lower()}_object'

        if target not in ('get_object',):
            target_args['Body'] = request.data
        parts = request.view_args['proxy_args'].split('/')

        target_args['Bucket'] = parts[0]
        target_args['Key'] = request.view_args['proxy_args'].removeprefix(parts[0]+'/')

        return target

    def _get_path(self, Bucket, Key):
        return os.path.join(self.buckets[Bucket]['path'], Key)

    # ------------------------------
    #     LOW LEVEL S3 (client)
    # ------------------------------

    def get_object(self, Bucket, Key):
        to_path = self._get_path(Bucket, Key)

        if not os.path.exists(to_path):
            return "", 404

        return '__FILE__', to_path

    def put_object(self, Body: bytes | BinaryIO, Bucket, Key):
        to_path = self._get_path(Bucket, Key)

        to_dir = os.path.dirname(to_path)
        if not os.path.exists(to_dir):
            os.makedirs(to_dir)

        if isinstance(Body, bytes):
            with open(to_path, "wb") as fh:
                fh.write(Body)
        else:
            # todo: does this ever occur when boto3 is not mocked?
            raise NotImplementedError()
            with open(to_path, 'b') as fh:
                shutil.copyfileobj(Body, fh)
                #fh.write(Body.read())

        return "", 200

    # ------------------------------
    #    HIGH LEVEL S3 (resource)
    # ------------------------------

    def upload_fileobj(self, Fileobj, Bucket, Key, ExtraArgs=None, Callback=None, Config=None):
        self.put_object(Fileobj, Bucket, Key)

        # todo: apply meta tags & callback

    def upload_file(self, Filename, Bucket, Key):
        # with open(Filename, 'b') as fh:
        #     self.upload_fileobj(fh, **kwargs)

        # since it's not remote we can just copy the file
        to_path = self._get_path(Bucket, Key)

        if os.path.samefile(to_path, Filename):
            # noop, used in dev environments
            return

        to_dir = os.path.dirname(to_path)
        if not os.path.exists(to_dir):
            os.makedirs(to_dir)

        shutil.copy(Filename, to_path)

    def download_file(self, Bucket, Key, Filename, ExtraArgs=None, Callback=None, Config=None):
        from_path = self._get_path(Bucket, Key)

        if os.path.exists(from_path) and os.path.exists(Filename) and \
            os.path.samefile(from_path, Filename):
            # noop, used in dev environments
            return

        to_dir = os.path.dirname(from_path)
        if not os.path.exists(to_dir):
            os.makedirs(to_dir)

        if not os.path.exists(from_path):
            # todo: throw proper boto3 exception
            raise Exception("S3 adapter: path not found: " + from_path)

        shutil.copy(from_path, Filename)

        # todo: apply meta tags & callback
