import datetime


DESCRIBE_DBINSTANCES_RESPONSE = {
    "DBInstances": [
        {
            "AllocatedStorage": 1,
            "AutoMinorVersionUpgrade": True,
            "AvailabilityZone": "us-east-1e",
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
                        "SubnetIdentifier": "subnet-abcd",
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
