import datetime

DESCRIBE_DBCLUSTERS_RESPONSE = {
    'DBClusters': [
        {
            'AllocatedStorage': 1,
            'AvailabilityZones': [
                'us-east-1e',
            ],
            'region': 'us-east-1',
            'BackupRetentionPeriod': 35,
            'CharacterSetName': 'utf8',
            'DatabaseName': 'prodprodDB',
            'DBClusterIdentifier': 'some-prod-db-iad',
            'DBClusterParameterGroup': 'some-param-group',
            'DBSubnetGroup': 'subnet-group-1',
            'Status': 'available',
            'PercentProgress': '10',
            'EarliestRestorableTime': '2021-06-10 00:05:53.316000+00:00',
            'Endpoint': 'some-prod-db-iad-0.subdomain.us-east-1.rds.amazonaws.com',
            'ReaderEndpoint': 'some-prod-ro-db-iad-0.subdomain.us-east-1.rds.amazonaws.com',
            'CustomEndpoints': [],
            'MultiAZ': False,
            'Engine': 'docdb',
            'EngineVersion': '3.6.0',
            'LatestRestorableTime': '2021-06-17 07:11:29.507000+00:00',
            'Port': 27017,
            'MasterUsername': 'test_user',
            'DBClusterOptionGroupMemberships': [],
            'PreferredBackupWindow': '03:36-04:06',
            'PreferredMaintenanceWindow': 'fri:04:01-fri:04:31',
            'ReadReplicaIdentifiers': [],
            'DBClusterMembers': [
                {
                    'DBInstanceIdentifier': 'some-prod-db-iad-0',
                    'IsClusterWriter': True,
                    # not sure what a proper value is here.
                    'DBClusterParameterGroupStatus': 'some_status',
                    'PromotionTier': 1,
                },
            ],
            'VpcSecurityGroups': [],
            'HostedZoneId': 'hostedzone',
            'StorageEncrypted': True,
            'DbClusterResourceId': 'cluster-abcde',
            'DBClusterArn': 'arn:aws:rds:us-east-1:some-arn:cluster:some-prod-db-iad-0',
            'AssociatedRoles': [],
            'IAMDatabaseAuthenticationEnabled': False,
            'ClusterCreateTime': '2020-06-04 14:26:48.271000+00:00',
            'EnabledCloudwatchLogsExports': [],
            'Capacity': 1,
            'EngineMode': 'provisioned',
            'ScalingConfigurationInfo': {
                'MinCapacity': 1,
                'MaxCapacity': 2,
                'AutoPause': True,
                'SecondsUntilAutoPause': 10,
                'TimeoutAction': 'ForceApplyCapacityChange',
            },
            'DeletionProtection': True,
            'HttpEndpointEnabled': False,
            'TagList': [],
        },
    ],
}

DESCRIBE_DBINSTANCES_RESPONSE = {
    "DBInstances": [
        {
            "AllocatedStorage": 1,
            "AutoMinorVersionUpgrade": True,
            "AvailabilityZone": "us-east-1e",
            'region': 'us-east-1',
            "BackupRetentionPeriod": 35,
            "CACertificateIdentifier": "abc-ca-2013",
            "CopyTagsToSnapshot": False,
            "DBClusterIdentifier": "some-prod-db-iad",
            "DBInstanceArn": "arn:aws:rds:us-east-1:some-arn:db:some-prod-db-iad-0",
            "DBInstanceClass": "db.r4.xlarge",
            "DBInstanceIdentifier": "some-prod-db-iad-0",
            "DBInstanceStatus": "available",
            "DBName": "prodprodDB",
            "DBParameterGroups": [
                {
                    "DBParameterGroupName": "default.aurora-postgresql9.6",
                    "ParameterApplyStatus": "in-sync",
                },
            ],
            "DBSecurityGroups": [],
            "DBSubnetGroup": {
                "DBSubnetGroupDescription": "subnet-group-1",
                "DBSubnetGroupName": "subnet-group-1",
                "SubnetGroupStatus": "Complete",
                "Subnets": [
                    {
                        "SubnetAvailabilityZone": {
                            "Name": "us-east-1a",
                        },
                        "SubnetIdentifier": "subnet-020b2f3928f190ce8",
                        "SubnetStatus": "Active",
                    },
                    {
                        "SubnetAvailabilityZone": {
                            "Name": "us-east-1d",
                        },
                        "SubnetIdentifier": "subnet-3421",
                        "SubnetStatus": "Active",
                    },
                    {
                        "SubnetAvailabilityZone": {
                            "Name": "us-east-1e",
                        },
                        "SubnetIdentifier": "subnet-4567",
                        "SubnetStatus": "Active",
                    },
                    {
                        "SubnetAvailabilityZone": {
                            "Name": "us-east-1e",
                        },
                        "SubnetIdentifier": "subnet-1234",
                        "SubnetStatus": "Active",
                    },
                ],
                "VpcId": "vpc-some-vpc",
            },
            "DbInstancePort": 0,
            "DomainMemberships": [],
            "Endpoint": {
                "Address": "some-prod-db-iad-0.subdomain.us-east-1.rds.amazonaws.com",
                "HostedZoneId": "hostedzone",
                "Port": 5432,
            },
            "Engine": "aurora-postgresql",
            "EngineVersion": "9.6.8",
            "EnhancedMonitoringResourceArn": "some-monitoring-arn",
            "IAMDatabaseAuthenticationEnabled": False,
            "InstanceCreateTime": datetime.datetime(2018, 8, 15, 1, 58, 59, 852000),
            "KmsKeyId": "arn:aws:kms:us-east-1:some-arn:key/some-guid",
            "LicenseModel": "postgresql-license",
            "MasterUsername": "prodprod",
            "MonitoringInterval": 60,
            "MonitoringRoleArn": "arn:aws:iam::some-arn:role/rds-monitoring-role",
            "MultiAZ": False,
            "OptionGroupMemberships": [
                {
                    "OptionGroupName": "default:aurora-postgresql-9-6",
                    "Status": "in-sync",
                },
            ],
            "PendingModifiedValues": {},
            "PerformanceInsightsEnabled": False,
            "PreferredBackupWindow": "03:36-04:06",
            "PreferredMaintenanceWindow": "fri:04:01-fri:04:31",
            "PromotionTier": 0,
            "PubliclyAccessible": False,
            "ReadReplicaDBInstanceIdentifiers": [],
            "StorageEncrypted": True,
            "StorageType": "aurora",
            "VpcSecurityGroups": [
                {
                    "Status": "active",
                    "VpcSecurityGroupId": "sg-some-othersg",
                },
                {
                    "Status": "active",
                    "VpcSecurityGroupId": "sg-some-sg",
                },
                {
                    "Status": "active",
                    "VpcSecurityGroupId": "sg-secgroup",
                },
            ],
        },
    ],
}
DESCRIBE_SECURITY_GROUPS_RESPONSE = [
    {
        'region': 'us-east-1',
        "OwnerId": "123456789012",
        "DBSecurityGroupName": "mysecgroup",
        "DBSecurityGroupDescription": "My Test Security Group",
        "VpcId": "vpc-1234567f",
        "EC2SecurityGroups": [],
        "IPRanges": [],
        "DBSecurityGroupArn": "arn:aws:rds:us-east-1:111122223333:secgrp:mysecgroup"
    }
]
DESCRIBE_SNAPSHOTS_RESPONSE = [
    {
        "DBSnapshotIdentifier": "mydbsnapshot",
        "DBInstanceIdentifier": "mysqldb",
        'region': 'us-east-1',
        'name': 'mydbsnapshot',
        "SnapshotCreateTime": "2018-02-08T22:28:08.598Z",
        "Engine": "mysql",
        "AllocatedStorage": 20,
        "Status": "available",
        "Port": 3306,
        "AvailabilityZone": "us-east-1f",
        "VpcId": "vpc-6594f31c",
        "InstanceCreateTime": "2018-02-08T22:24:55.973Z",
        "MasterUsername": "mysqladmin",
        "EngineVersion": "5.6.37",
        "LicenseModel": "general-public-license",
        "SnapshotType": "manual",
        "OptionGroupName": "default:mysql-5-6",
        "PercentProgress": 100,
        "StorageType": "gp2",
        "Encrypted": False,
        "DBSnapshotArn": "arn:aws:rds:us-east-1:123456789012:snapshot:mydbsnapshot",
        "IAMDatabaseAuthenticationEnabled": False,
        "ProcessorFeatures": [],
        "DbiResourceId": "db-AKIAIOSFODNN7EXAMPLE"
    }
]

DESCRIBE_DBSNAPSHOTS_RESPONSE = {
    "DBSnapshots": [
        {
            "DBSnapshotIdentifier": "some-db-snapshot-identifier",
            "DBInstanceIdentifier": "some-prod-db-iad-0",
            "SnapshotCreateTime": datetime.datetime(2022, 8, 15, 1, 58, 59, 852000),
            "Engine": "aurora-postgresql",
            "AllocatedStorage": 1,
            "Status": "available",
            "Port": 27017,
            "AvailabilityZone": "us-east-1e",
            "VpcId": "vpc-some-vpc",
            "InstanceCreateTime": datetime.datetime(2021, 8, 15, 1, 58, 59, 852000),
            "MasterUsername": "test_user",
            "EngineVersion": "3.6.0",
            "LicenseModel": "postgresql-license",
            "SnapshotType": "automated",
            "Iops": 1234,
            "OptionGroupName": "default:aurora-postgresql-9-6",
            "PercentProgress": 10,
            "SourceRegion": "us-eat-1",
            "SourceDBSnapshotIdentifier": "some-source-db-snapshot-identifier",
            "StorageType": "aurora",
            "TdeCredentialArn": "some-tde-credential-arn",
            "Encrypted": True,
            "KmsKeyId": "arn:aws:kms:us-east-1:some-arn:key/some-guid",
            "DBSnapshotArn": "arn:aws:rds:us-east-1:some-arn:snapshot:some-prod-db-iad-0",
            "Timezone": "utc",
            "IAMDatabaseAuthenticationEnabled": True,
            "ProcessorFeatures": [],
            "DbiResourceId": "some-dbi-resource-id",
            "TagList": [],
            "OriginalSnapshotCreateTime": datetime.datetime(2022, 1, 1),
            "SnapshotDatabaseTime": datetime.datetime(2022, 1, 1),
            "SnapshotTarget": "some-snapshot-target",
            "StorageThroughput": 1234,
        },
        {
            "DBSnapshotIdentifier": "some-other-db-snapshot-identifier",
            "DBInstanceIdentifier": "some-prod-db-iad-0",
            "SnapshotCreateTime": datetime.datetime(2022, 8, 15, 1, 58, 59, 852000),
            "Engine": "aurora-postgresql",
            "AllocatedStorage": 1,
            "Status": "available",
            "Port": 27017,
            "AvailabilityZone": "us-east-1e",
            "VpcId": "vpc-some-vpc",
            "InstanceCreateTime": datetime.datetime(2021, 8, 15, 1, 58, 59, 852000),
            "MasterUsername": "test_user",
            "EngineVersion": "3.6.0",
            "LicenseModel": "postgresql-license",
            "SnapshotType": "automated",
            "Iops": 1234,
            "OptionGroupName": "default:aurora-postgresql-9-6",
            "PercentProgress": 10,
            "SourceRegion": "us-eat-1",
            "SourceDBSnapshotIdentifier": "some-other-source-db-snapshot-identifier",
            "StorageType": "aurora",
            "TdeCredentialArn": "some-tde-credential-arn",
            "Encrypted": True,
            "KmsKeyId": "arn:aws:kms:us-east-2:some-arn:key/some-guid",
            "DBSnapshotArn": "arn:aws:rds:us-east-2:some-arn:snapshot:some-prod-db-iad-0",
            "Timezone": "utc",
            "IAMDatabaseAuthenticationEnabled": True,
            "ProcessorFeatures": [],
            "DbiResourceId": "some-dbi-resource-id",
            "TagList": [],
            "OriginalSnapshotCreateTime": datetime.datetime(2022, 1, 1),
            "SnapshotDatabaseTime": datetime.datetime(2022, 1, 1),
            "SnapshotTarget": "some-snapshot-target",
            "StorageThroughput": 1234,
        },
    ],
}


DESCRIBE_DBSNAPSHOT_ATTRIBUTE_RESPONSE = [
    {
        'DBSnapshotIdentifier': 'some-db-snapshot-identifier',
        'DBSnapshotAttributes': [
            {
                'AttributeName': 'backup',
                'AttributeValues': [
                    'all',
                ]
            },
            {
                'AttributeName': 'attrib-1',
                'AttributeValues': [
                    'all',
                ]
            }
        ]
    },
    {
        'DBSnapshotIdentifier': 'some-other-db-snapshot-identifier',
        'DBSnapshotAttributes': [
            {
                'AttributeName': 'backup',
                'AttributeValues': [
                    'all',
                ]
            },
            {
                'AttributeName': 'attrib-1',
                'AttributeValues': [
                    'all',
                ]
            },
            {
                'AttributeName': 'restore',
                'AttributeValues': [
                    'all',
                ]
            }
        ]
    }
]
