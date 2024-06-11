TEST_DATAFLOW_JOBS = [
    {
        'createTime': '2020-04-02T14:00:00.0000Z',
        'location': 'us-central1',
        'name': 'job1',
        'id': 'job1',
        'type': 'JOB_TYPE_BATCH',
        'environment': {
            'clusterManagerApiService': 'c1',
            'dataset': 'bigquerydataset',
            'serviceAccountEmail': 'default',
            'serviceKmsKeyName:': 'projects/project-123/locations/us-central1/keyRings/key_ring1/cryptoKeys/key1',
            'shuffleMode': 'VM_BASED',
            'workerRegion': 'us-central1',
            'workerZone': 'us-central1-a',
        },
        'startTime': '2020-04-02T14:00:00.0000Z',
        'currentState': 'JOB_STATE_RUNNING',
        'requestedState': 'JOB_STATE_DONE',
        'consolelink': '',
        'satisfiesPzs': True,
        'bigTables': ['table123', 'table456'],
        'bigQueries': ['table1', 'table2'],
        'pubSub': [{'topicId': 'projects/project123/topic/topic123', 'subscriptionId': 'projects/project123/subscriptions/sub123'}],
        'spannerDatabases': ['projects/project-123/instances/instance1/databases/database1', 'projects/project-123/instances/instance1/databases/database2'],
    },
]