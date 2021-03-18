from statsd import StatsClient
from statsd.client.timer import Timer


class ScopedStatsClient(object):
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

    def __init__(self, client: StatsClient, prefix: str = None):
        self._client = client
        self._scope_prefix = prefix

    def get_scoped_stats_client(self, scope: str):
        if not self._scope_prefix:
            prefix = scope
        else:
            prefix = self._scope_prefix + "." + scope
        return ScopedStatsClient(self._client, prefix)

    def is_enabled(self) -> bool:
        return self._client is not None

    def incr(self, stat: str, count: int = 1, rate: float = 1.0):
        if self.is_enabled():
            self._client.incr(self._scope_prefix + "." + stat, count, rate)

    def timer(self, stat: str, rate: float = 1.0) -> Timer:
        if self.is_enabled():
            return self._client.timer(stat, rate)
        return None
