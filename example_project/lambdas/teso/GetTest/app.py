import os
import boto3
import testlayer


def handler(event, context):
    return {
        "testlayer": testlayer.get_id(),
        "boto3_mocked": hasattr(boto3, '__TOMCRU__'),
        "envvar": os.getenv('tesomsz'),
        "event": list(event.keys()),
        "remaining_time": context.get_remaining_time_in_millis() / 1000.0 / 60
    }
