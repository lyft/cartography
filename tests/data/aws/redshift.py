import datetime

CLUSTERS = [
    {
        'AllowVersionUpgrade': True,
        'AutomatedSnapshotRetentionPeriod': 35,
        'AvailabilityZone': 'us-east-1e',
        'region': 'us-east-1',
        'ClusterCreateTime': datetime.datetime(2018, 9, 12, 0, 19, 33, 652000),
        'ClusterIdentifier': 'my-cluster',
        'ClusterNodes': [
            {
                'NodeRole': 'LEADER',
                'PrivateIPAddress': '10.0.34.72',
                'PublicIPAddress': '1.2.3.4',
            },
            {
                'NodeRole': 'COMPUTE-0',
                'PrivateIPAddress': '10.0.45.66',
                'PublicIPAddress': '2.3.4.5',
            },
        ],
        'ClusterParameterGroups': [
            {
                'ClusterParameterStatusList': [
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'enable_user_activity_logging',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'max_cursor_result_set_size',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'query_group',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'datestyle',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'extra_float_digits',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'search_path',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'statement_timeout',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'wlm_json_configuration',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'require_ssl',
                    },
                    {
                        'ParameterApplyStatus': 'in-sync',
                        'ParameterName': 'use_fips_ssl',
                    },
                ],
                'ParameterApplyStatus': 'in-sync',
                'ParameterGroupName': 'my-cluster',
            },
        ],
        'ClusterPublicKey': 'ssh-rsa AAAA Amazon-Redshift\n',
        'ClusterRevisionNumber': '15503',
        'ClusterSecurityGroups': [],
        'ClusterStatus': 'available',
        'ClusterSubnetGroupName': 'redshift',
        'ClusterVersion': '1.0',
        'DBName': 'dev',
        'DeferredMaintenanceWindows': [],
        'ElasticResizeNumberOfNodeOptions': '[2,3,5,6,7,8]',
        'Encrypted': True,
        'Endpoint': {
            'Address': 'my-cluster.abc.us-east-1.redshift.amazonaws.example.com',
            'Port': 5439,
        },
        'EnhancedVpcRouting': False,
        'IamRoles': [{
            'ApplyStatus': 'in-sync',
            'IamRoleArn': 'arn:aws:iam::1111:role/my-redshift-iam-role',
        }],
        'KmsKeyId': 'arn:aws:kms:us-east-1:1111:key/GUID',
        'MaintenanceTrackName': 'trailing',
        'ManualSnapshotRetentionPeriod': -1,
        'MasterUsername': 'masteruser',
        'NodeType': 'ds2.8xlarge',
        'NumberOfNodes': 2,
        'PendingModifiedValues': {},
        'PreferredMaintenanceWindow': 'wed:09:00-wed:09:30',
        'PubliclyAccessible': True,
        'Tags': [],
        'VpcId': 'my_vpc',
        'VpcSecurityGroups': [
            {
                'Status': 'active',
                'VpcSecurityGroupId': 'sg-028e2522c72719996',
            },
        ],
    },
]

NODES = [
    {
        "arn": 'arn:aws:redshift:us-east-1:1111:reserved-node/1ba8e2e3-bc01-4d65-b35d-a4a3e931547e',
        'region': 'us-east-1',
        "OfferingType": "Heavy Utilization",
        "FixedPrice": "",
        "NodeType": "dw.hs1.xlarge",
        "ReservedNodeId": "1ba8e2e3-bc01-4d65-b35d-a4a3e931547e",
        "UsagePrice": "",
        "RecurringCharges": [
            {
                "RecurringChargeAmount": "",
                "RecurringChargeFrequency": "Hourly",
            },
        ],
        "NodeCount": 1,
        "State": "payment-pending",
        "StartTime": "2013-02-13T17:08:39.051Z",
        "Duration": 31536000,
        "ReservedNodeOfferingId": "ceb6a579-cf4c-4343-be8b-d832c45ab51c",
    },
]
