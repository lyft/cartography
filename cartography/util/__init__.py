import logging


logger = logging.getLogger(__name__)

# The statsd client used for observability.  This is `None` unless cartography.config.statsd_enabled is True.
stats_client = None
