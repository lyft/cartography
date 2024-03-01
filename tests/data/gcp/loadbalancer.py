TEST_GLOBAL_HEALTH_CHECK = [
    {
        'name': 'globalcheck123',
        'id': 'projects/project123/global/healthChecks/globalcheck123',
        'region': 'global',
        'type': 'global',
        'checkIntervalSec': 5,
        'timeoutSec': 10,
    },
]

TEST_REGIONAL_HEALTH_CHECK = [
    {
        'name': 'regionalcheck123',
        'id': 'projects/project123/regions/us-east1/healthChecks/regionalcheck123',
        'region': 'us-east1',
        'type': 'regional',
        'checkIntervalSec': 5,
        'timeoutSec': 10,
    },
]

TEST_GLOBAL_INSTANCE_GROUP = [
    {
        'name': 'globalgroup123',
        'id': 'projects/project123/zones/us-east1-a/instanceGroups/globalgroup123',
        'region': 'global',
        'type': 'global',
        'size': 3,
        'network': 'default',
        'subnetwork': 'default',
    },
]

TEST_REGIONAL_INSTANCE_GROUP = [
    {
        'name': 'regionalgroup123',
        'id': 'projects/project123/regions/us-east1/instanceGroups/regionalgroup123',
        'region': 'us-east1',
        'type': 'regional',
        'size': 3,
        'network': 'default',
        'subnetwork': 'default',
    },
]

TEST_GLOBAL_URL_MAP = [
    {
        "name": "globalmap123",
        "id": "projects/project123/global/urlmaps/globalmap123",
        "defaultService": "service123",
        "type": "global",
    },
]

TEST_REGIONAL_URL_MAP = [
    {
        "name": "regionalmap123",
        "id": "projects/project123/regions/us-east1-a/urlmaps/regionalmap123",
        "region": "us-east1-a",
        "defaultService": "service123",
        "type": "regional",
    },
]

TEST_SSL_POLICY = [
    {
        "name": 'sslpolicy123',
        'id': 'projects/project123/global/urlmaps/sslpolicy123',
        'minTlsVersion': 'TLS1.1',
    },
]
