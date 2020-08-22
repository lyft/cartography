import logging
import sys


if sys.version_info >= (3, 7):
    from importlib.resources import open_binary
else:
    from importlib_resources import open_binary

logger = logging.getLogger(__name__)


def load_resource_binary(package, resource_name):
    return open_binary(package, resource_name)


# The statsd client used for observability.  This is `None` unless cartography.config.statsd_enabled is True.
stats_client = None
