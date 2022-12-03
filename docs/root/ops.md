# Cartography operations guide

This document contains tips for running Cartography in production.

## Maintaining a up-to-date picture of your infrastructure

Running `cartography` ensures that your Neo4j instance contains the most recent snapshot of your infrastructure. Here's
how that process works.

### Update tags

Each sync run has an `update_tag` associated with it,
which is the [Unix timestamp of when the sync started](https://github.com/lyft/cartography/blob/8d60311a10156cd8aa16de7e1fe3e109cc3eca0f/cartography/sync.py#L131-L134).
See our [docs for more details](../dev/writing-intel-modules.md#handling-cartographys-update_tag).

### Cleanup jobs

Each node and relationship created or updated during the sync will have their `lastupdated` field set to the
`update_tag`. At the end of a sync run, nodes and relationships with out-of-date `lastupdated` fields are considered
stale and will be deleted via a [cleanup job](../dev/writing-intel-modules.md#cleanup).

### Sync frequency

To keep data updated, you can run `cartography` as part of a periodic script (cronjobs in Linux, scheduled tasks in
Windows). Determine your needs for data freshness and adjust accordingly.

## Observability

### statsd

Cartography can be configured to send metrics to a [statsd](https://github.com/statsd/statsd) server. Specify the
`--statsd-enabled` flag when running `cartography` for sync execution times to be recorded and sent to
`127.0.0.1:8125` by default (these options are also configurable with the `--statsd-host` and `--statsd-port` options).
You can also provide your own `--statsd-prefix` to make these metrics easier to find in your own environment.

## Docker image

A production-ready docker image is available in [GitHub Container Registry](https://github.com/lyft/cartography/pkgs/container/cartography). We recommend that you avoid using the `:latest` tag and instead
use the tag or digest associated with your desired release version, e.g.

```bash
docker pull ghcr.io/lyft/cartography:0.61.0
```

This image can then be ran with any of your desired command line flags:

```bash
docker run --rm ghcr.io/lyft/cartography:0.61.0 --help
```
