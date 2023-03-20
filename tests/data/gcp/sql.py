CLOUD_SQL_INSTANCES = [
    {
        'id': 'instance123',
        'state': 'RUNNABLE',
        'databaseVersion': 'MYSQL_5_7',
        'masterInstanceName': 'instance123',
        'maxDiskSize': '256GB',
        'currentDiskSize': '128GB',
        'instanceType': 'CLOUD_SQL_INSTANCE',
        'connectionName': 'instance123',
        'name': 'sqlinstance123',
        'region': 'us-west',
        'gceZone': 'us-west-1a',
        'secondaryGceZone': 'us-west-1b',
        'satisfiesPzs': True,
        'authorizedNetworksList': [
            '0.0.0.0/0', '192.168.10.1',
        ],
        'createTime': '2021-10-15T16:19:00.094Z',
    },
    {
        'id': 'instance456',
        'state': 'RUNNABLE',
        'databaseVersion': 'MYSQL_5_7',
        'masterInstanceName': 'instance456',
        'maxDiskSize': '256GB',
        'currentDiskSize': '128GB',
        'instanceType': 'CLOUD_SQL_INSTANCE',
        'connectionName': 'instance456',
        'name': 'sqlinstance456',
        'region': 'us-east',
        'gceZone': 'us-east-1a',
        'secondaryGceZone': 'us-east-1b',
        'satisfiesPzs': True,
        'authorizedNetworksList': [
            '192.168.10.1',
        ],
        'createTime': '2021-9-9T16:19:00.094Z',
    },
]

CLOUD_SQL_USERS = [
    {
        'name': 'user123',
        'id': 'user123',
        'instance_id': 'instance123',
        'host': 'sqlserver123',
        'instance': 'instance123',
        'project': 'abcdefg4567',
        'type': 'databasereader',
    },
    {
        'name': 'user456',
        'id': 'user456',
        'instance_id': 'instance456',
        'host': 'sqlserver456',
        'instance': 'instance456',
        'project': 'abcdefg4567',
        'type': 'databasewriter',
    },
]

CLOUD_SQL_DATABASES = [
    {
        'name': 'database-123',
        'id': 'database-123',
        'instance_id': 'instance123',
        'host': 'sqlserver123',
        'instance': 'instance123',
        'project': 'abcdefg4567',
        'type': 'databasereader',
    },
    {
        'name': 'database-456',
        'id': 'database-456',
        'instance_id': 'instance456',
        'host': 'sqlserver456',
        'instance': 'instance456',
        'project': 'abcdefg4567',
        'type': 'databasewriter',
    },
]
