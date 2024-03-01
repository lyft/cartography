CLOUDTASKS_QUEUES = [
    {
        "appEngineRoutingOverride": {
            "host": "project-123.appspot.com",
            "instance": "app instance",
            "service": "app service",
            "version": "1.0.0",
        },
        "region": "us-central1",
        "id": "projects/project-123/locations/us-central1/queues/queue1",
        "queue_name": "queue1",
        "name": "projects/project-123/locations/us-central1/queues/queue1",
        "purgeTime": "2014-10-02T15:01:23Z",
        "rateLimits": {
            "maxBurstSize": 42,
            "maxConcurrentDispatches": 42,
            "maxDispatchesPerSecond": 3.14,
        },
        "retryConfig": {
            "maxAttempts": 42,
            "maxBackoff": "10.0s",
            "maxDoublings": 42,
            "maxRetryDuration": "15.0s",
            "minBackoff": "3.5s",
        },
        "state": "RUNNING",
    },
    {
        "appEngineRoutingOverride": {
            "host": "project-123.appspot.com",
            "instance": "app instance",
            "service": "app service",
            "version": "1.0.0",
        },
        "region": "us-central2",
        "id": "projects/project-123/locations/us-central1/queues/queue2",
        "queue_name": "queue2",
        "name": "projects/project-123/locations/us-central1/queues/queue2",
        "purgeTime": "2014-10-02T15:01:23Z",
        "rateLimits": {
            "maxBurstSize": 42,
            "maxConcurrentDispatches": 42,
            "maxDispatchesPerSecond": 3.14,
        },
        "retryConfig": {
            "maxAttempts": 42,
            "maxBackoff": "10.0s",
            "maxDoublings": 42,
            "maxRetryDuration": "15.0s",
            "minBackoff": "3.5s",
        },
        "state": "PAUSED",
    },
]
