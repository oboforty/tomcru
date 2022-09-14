from datetime import datetime
import time


class EmeLambdaContext:

    def __init__(self, **kwargs):
        self.start = time.time()

    def get_remaining_time_in_millis(self):
        # todo: how to get max time?
        return (12*1000*3600) - 1000*(time.time()-self.start)

    @property
    def function_name(self):
        return None
    @property
    def function_version(self):
        return None
    @property
    def invoked_function_arn(self):
        return None
    @property
    def memory_limit_in_mb(self):
        return None
    @property
    def aws_request_id(self):
        return None
    @property
    def log_group_name(self):
        return None
    @property
    def log_stream_name(self):
        return None
