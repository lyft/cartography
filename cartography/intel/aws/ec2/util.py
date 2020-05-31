import botocore.config


# TODO memoize this
def get_botocore_config():
    return botocore.config.Config(
        read_timeout=360,
        retries={
            'max_attempts': 10,
        },
    )
