import boto3
#import testlayer


def handler(event, context):
    return {
        #"testlayer": testlayer.generate_id(),
        "boto3_mocked": hasattr(boto3, '__TOMCRU__'),
        #"event": event
    }
