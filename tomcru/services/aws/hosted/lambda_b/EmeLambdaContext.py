from datetime import datetime
import time


class EmeLambdaContext:
    def __init__(self, ctx_cfg: dict):
        self.max_lambda_time_ms = ctx_cfg.get('timeout', 900)
        self.start = time.time()

    def get_remaining_time_in_millis(self):
        return self.max_lambda_time_ms - 1000*(time.time()-self.start)

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
