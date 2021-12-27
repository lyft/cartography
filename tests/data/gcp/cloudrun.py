CLOUDRUN_AUTHORIZED_DOMAINS = [
    {
        'id': 'example123.com',
    },
    {
        'id': 'example456.com',
    },
]
CLOUDRUN_CONFIGURATIONS = [
    {
        'id': 'configuration123',
        'metadata': {
            'name': 'configuration123',
            'namespace': 'project123',
            'selfLink': 'example123.com/configuration123',
            'uid': 'configuration123',
            'resourceVersion': 'version1.1',
            'creationTimestamp': '2020-10-02T15:01:23Z',
            'deletionTimestamp': '2021-10-02T15:01:23Z',
            'clusterName': 'cluster123',
        },
        'spec': {
            'observedGeneration': 2,
            'latestCreatedRevisionName': 'revision1',
            'latestReadyRevisionName': 'revision2',
        },
    },
    {
        'id': 'configuration456',
        'metadata': {
            'name': 'configuration456',
            'namespace': 'project123',
            'selfLink': 'example123.com/configuration456',
            'uid': 'configuration456',
            'resourceVersion': 'version1.2',
            'creationTimestamp': '2019-10-02T15:01:23Z',
            'deletionTimestamp': '2020-10-02T15:01:23Z',
            'clusterName': 'cluster456',
        },
        'spec': {
            'observedGeneration': 3,
            'latestCreatedRevisionName': 'revision1',
            'latestReadyRevisionName': 'revision2',
        },
    },
]
CLOUDRUN_DOMAIN_MAPPINGS = [
    {
        'id': 'domainmap123',
        'metadata': {
            'name': 'domainmap123',
            'namespace': 'project123',
            'selfLink': 'example123.com/domainmap123',
            'uid': 'domainmap123',
            'resourceVersion': 'version1.1',
            'creationTimestamp': '2020-10-02T15:01:23Z',
            'deletionTimestamp': '2021-10-02T15:01:23Z',
        },
        'spec': {
            'routeName': 'route123',
            'certificateMode': 'AUTOMATIC',
            'forceOverride': True,
        },
    },
    {
        'id': 'domainmap456',
        'metadata': {
            'name': 'domainmap456',
            'namespace': 'project123',
            'selfLink': 'example123.com/domainmap456',
            'uid': 'domainmap456',
            'resourceVersion': 'version1.2',
            'creationTimestamp': '2019-10-02T15:01:23Z',
            'deletionTimestamp': '2020-10-02T15:01:23Z',
        },
        'spec': {
            'routeName': 'route456',
            'certificateMode': 'AUTOMATIC',
            'forceOverride': True,
        },
    },
]
CLOUDRUN_REVISIONS = [
    {
        'id': 'revision123',
        'metadata': {
            'name': 'revision123',
            'namespace': 'project123',
            'selfLink': 'example123.com/revision123',
            'uid': 'revision123',
            'resourceVersion': 'version1.1',
            'creationTimestamp': '2020-10-02T15:01:23Z',
            'deletionTimestamp': '2021-10-02T15:01:23Z',
        },
        'spec': {
            'containerConcurrency': 80,
            'timeoutSeconds': 300,
        },
    },
    {
        'id': 'revision456',
        'metadata': {
            'name': 'revision456',
            'namespace': 'project123',
            'selfLink': 'example123.com/revision456',
            'uid': 'revision456',
            'resourceVersion': 'version1.2',
            'creationTimestamp': '2019-10-02T15:01:23Z',
            'deletionTimestamp': '2020-10-02T15:01:23Z',
        },
        'spec': {
            'containerConcurrency': 80,
            'timeoutSeconds': 300,
        },
    },
]
CLOUDRUN_ROUTES = [
    {
        'id': 'route123',
        'metadata': {
            'name': 'route123',
            'namespace': 'project123',
            'selfLink': 'example123.com/route123',
            'uid': 'route123',
            'resourceVersion': 'version1.1',
            'creationTimestamp': '2020-10-02T15:01:23Z',
            'deletionTimestamp': '2021-10-02T15:01:23Z',
        },
        'status': {
            'observedGeneration': 2,
            'url': 'example123.com',
        },
    },
    {
        'id': 'route456',
        'metadata': {
            'name': 'route456',
            'namespace': 'project123',
            'selfLink': 'example123.com/route456',
            'uid': 'route456',
            'resourceVersion': 'version1.2',
            'creationTimestamp': '2019-10-02T15:01:23Z',
            'deletionTimestamp': '2020-10-02T15:01:23Z',
        },
        'status': {
            'observedGeneration': 3,
            'url': 'example123.com',
        },
    },
]
CLOUDRUN_SERVICES = [
    {
        'id': 'service123',
        'metadata': {
            'name': 'service123',
            'namespace': 'project123',
            'selfLink': 'example123.com/service123',
            'uid': 'service123',
            'resourceVersion': 'version1.1',
            'creationTimestamp': '2020-10-02T15:01:23Z',
            'deletionTimestamp': '2021-10-02T15:01:23Z',
        },
        'status': {
            'observedGeneration': 1,
            'latestReadyRevisionName': 'revision1.1',
            'latestCreatedRevisionName': 'revision1.2',
        },
    },
    {
        'id': 'service456',
        'metadata': {
            'name': 'service456',
            'namespace': 'project123',
            'selfLink': 'example123.com/service456',
            'uid': 'service456',
            'resourceVersion': 'version1.2',
            'creationTimestamp': '2019-10-02T15:01:23Z',
            'deletionTimestamp': '2020-10-02T15:01:23Z',
        },
        'status': {
            'observedGeneration': 2,
            'latestReadyRevisionName': 'revision1.2',
            'latestCreatedRevisionName': 'revision1.3',
        },
    },
]
