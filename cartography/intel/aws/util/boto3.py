import botocore.config


def get_botocore_config() -> botocore.config.Config:
    return botocore.config.Config(
        read_timeout=360,
        retries={
            'max_attempts': 10,
        },
    )
