TEST_INSTANCES = [
    {
        'config': 'projects/project-123/instanceConfigs/config1',
        'createTime': '2014-10-02T15:01:23Z',
        'displayName': 'instance1',
        'instanceType': 'PROVISIONED',
        'name': 'projects/project-123/instances/instance1',
        'nodeCount': 42,
        'processingUnits': 42,
        'state': 'READY',
        'updateTime': '2014-10-02T15:01:23Z'
    },
    {
        'config': 'projects/project-123/instanceConfigs/config2',
        'createTime': '2014-10-02T15:01:23Z',
        'displayName': 'instance2',
        'instanceType': 'PROVISIONED',
        'name': 'projects/project-123/instances/instance2',
        'nodeCount': 24,
        'processingUnits': 24,
        'state': 'READY',
        'updateTime': '2014-10-02T15:01:23Z'
    }
]

TEST_INSTANCE_CONFIG = [
    {
        "baseConfig": "projects/project-123/instanceConfigs/nam3",
        "configType": "GOOGLE_MANAGED",
        "displayName": "config1",
        "name": "projects/project-123/instanceConfigs/config1",
        "reconciling": True,
        "state": "READY",
    },
    {
        "baseConfig": "projects/project-123/instanceConfigs/nam3",
        "configType": "GOOGLE_MANAGED",
        "displayName": "config2",
        "name": "projects/project-123/instanceConfigs/config2",
        "reconciling": False,
        "state": "READY",
    }
]

TEST_INSTANCE_CONFIG_REPLICA = [
    {
        "defaultLeaderLocation": True,
        "location": "us-central1",
        "type": "READ_WRITE",
        "config": "projects/project-123/instanceConfigs/config1",
    },
    {
        "defaultLeaderLocation": True,
        "location": "us-central2",
        "type": "READ_WRITE",
        "config": "projects/project-123/instanceConfigs/config2",
    }
]

TEST_INSTANCE_DATABASE = [
    {
        "createTime": "2014-10-02T15:01:23Z",
        "databaseDialect": "GOOGLE_STANDARD_SQL",
        "defaultLeader": "dl",
        "earliestVersionTime": "2014-10-02T15:01:23.045123456Z",
        "encryptionConfig": {
            "kmsKeyName": "kmsKey",
        },
        "name": "projects/project-123/instances/instance1/databases/database1",
        "restoreInfo": {
            "backupInfo": {
                "backup": "projects/project-123/instances/instance1/backups/backup1",
            },
            "sourceType": "BACKUP",
        },
        "state": "READY",
        "versionRetentionPeriod": "3600",
    },
    {
        "createTime": "2014-10-02T15:01:23Z",
        "databaseDialect": "GOOGLE_STANDARD_SQL",
        "defaultLeader": "dl",
        "earliestVersionTime": "2014-10-02T15:01:23.045123456Z",
        "encryptionConfig": {
            "kmsKeyName": "kmsKey",
        },
        "encryptionInfo": [
            {
                "encryptionType": "GOOGLE_DEFAULT_ENCRYPTION",
                "kmsKeyVersion": "2.0.0",
            },
        ],
        "name": "projects/project-123/instances/instance1/databases/database2",
        "restoreInfo": {
            "backupInfo": {
                "backup": "projects/project-123/instances/instance1/backups/backup2",
            },
            "sourceType": "BACKUP",
        },
        "state": "READY",
        "versionRetentionPeriod": "3600",
    },
]

TEST_INSTANCE_BACKUP = [
    {
        "createTime": "2014-10-02T15:01:23Z",
        "database": "projects/project-123/instances/instance1/databases/database1",
        "databaseDialect": "GOOGLE_STANDARD_SQL",
        "encryptionInfo": {
            "encryptionType": "GOOGLE_DEFAULT_ENCRYPTION",
            "kmsKeyVersion": "2.0.0",
        },
        "expireTime": "2014-10-02T22:01:23Z",
        "maxExpireTime": "2014-11-02T22:01:23Z",
        "name": "projects/project-123/instances/instance1/backups/backup1",
        "sizeBytes": "512",
        "state": "READY",
        "versionTime": "2014-10-02T15:01:23.045123456Z",
    },
    {
        "createTime": "2014-10-02T15:01:23Z",
        "database": "projects/project-123/instances/instance1/databases/database2",
        "databaseDialect": "GOOGLE_STANDARD_SQL",
        "encryptionInfo": {
            "encryptionType": "GOOGLE_DEFAULT_ENCRYPTION",
            "kmsKeyVersion": "2.0.0",
        },
        "expireTime": "2014-10-02T22:01:23Z",
        "maxExpireTime": "2014-11-02T22:01:23Z",
        "name": "projects/project-123/instances/instance1/backups/backup2",
        "sizeBytes": "512",
        "state": "READY",
        "versionTime": "2014-10-02T15:01:23.045123456Z",
    },
]
