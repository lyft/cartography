import os

from settings.default import config as default_config
from settings.production import config as production_config


def get_config():
    return production_config if 'SERVICE_APP_ENV' in os.environ and os.environ['SERVICE_APP_ENV'] == 'production' else default_config
