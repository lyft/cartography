import logging

from statsd import StatsClient


logger = logging.getLogger(__name__)


class _StatsClientWrapper:
    def __init__(self, client: StatsClient):
        self._client = client

    def set_client(self, client: StatsClient) -> None:
        self._client = client

    def get_client(self) -> StatsClient:
        return self._client

    def is_enabled(self) -> bool:
        return self._client is not None


class ScopedStatsClient:
    """
    A Proxy object for an underlying statsd client.
    Adds a new call, get_scoped_stats_client(scope), which returns a new proxy to the same
    client which will prefix all calls to underlying methods with the scoped prefix:
    new_client = client.get_scoped_stats_client('a')
    new_client.incr('b') # Metric name = a.b
    This can be nested:
    newer_client = new_client.get_scoped_stats_client('subsystem')
    newer_client.incr('bad') # Metric name = a.subsystem.bad
    """

    def __init__(self, client: _StatsClientWrapper, prefix: str = None):
        self._client = client
        self._scope_prefix = prefix

    def get_stats_client(self, scope: str) -> 'ScopedStatsClient':
        """
        This method returns a new proxy to the same client
        which will prefix all calls to underlying methods with the scoped prefix
        """
        if not self._scope_prefix:
            prefix = scope
        else:
            prefix = f"{self._scope_prefix}.{scope}"
        return ScopedStatsClient(self._client, prefix)

    def is_enabled(self) -> bool:
        return self._client.is_enabled()

    def incr(self, stat: str, count: int = 1, rate: float = 1.0) -> None:
        """
        This method uses statsd to increment a counter.
        :param stat: the name of the counter metric stat (string) to increment
        :param count: the amount (integer) to increment by. May be negative
        :param rate: a sample rate, a float between 0 and 1. Will only send data this percentage of the time.
                             The statsd server will take the sample rate into account for counters
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            logger.info(f"Stat being incremented is {stat}")
            self._client.get_client().incr(stat, count, rate)

    def timer(self, stat: str, rate: float = 1.0):
        """
        This method uses statsd to retrieve a timer.
        When Timer.stop() is called, a timing stat will automatically be sent to statsd
        :param stat: the name of the timer metric stat (string) to report
        :param rate: a sample rate, a float between 0 and 1. Will only send data this percentage of the time.
                             The statsd server will take the sample rate into account for counters
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            return self._client.get_client().timer(stat, rate)
        return None

    def set_stats_client(self, stats_client: StatsClient) -> None:
        self._client.set_client(stats_client)


# Global _scoped_stats_client
# Will be set when cartography.config.statsd_enabled is True
_scoped_stats_client: ScopedStatsClient = ScopedStatsClient(_StatsClientWrapper(None))


def set_stats_client(stats_client: StatsClient) -> None:
    """
    This is used to set the module level stats client configured to talk with a statsd host
    """
    global _scoped_stats_client
    _scoped_stats_client.set_stats_client(stats_client)


def get_stats_client(prefix: str) -> ScopedStatsClient:
    """
    Returns a ScopedStatsClient object, which is a simple wrapper over statsd.client.Statsclient
    that allows one to scope down the metric as needed
    """
    return _scoped_stats_client.get_stats_client(prefix)
