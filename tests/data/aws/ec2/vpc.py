import datetime

DESCRIBE_VPCS = [
    {
        "CidrBlock": "30.1.0.0/16",
        "DhcpOptionsId": "dopt-19edf471",
        "State": "available",
        "VpcId": "vpc-0e9801d129EXAMPLE",
        "OwnerId": "111122223333",
        "InstanceTenancy": "default",
        "CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-cidr-assoc-062c64cfafEXAMPLE",
                "CidrBlock": "30.1.0.0/16",
                "CidrBlockState": {
                    "State": "associated"
                }
            }
        ],
        "IsDefault": False,
        "Tags": [
            {
                "Key": "Name",
                "Value": "Not Shared"
            }
        ]
    },
    {
        "CidrBlock": "10.0.0.0/16",
        "DhcpOptionsId": "dopt-19edf471",
        "State": "available",
        "VpcId": "vpc-06e4ab6c6cEXAMPLE",
        "OwnerId": "222222222222",
        "InstanceTenancy": "default",
        "CidrBlockAssociationSet": [
            {
                "AssociationId": "vpc-cidr-assoc-00b17b4eddEXAMPLE",
                "CidrBlock": "10.0.0.0/16",
                "CidrBlockState": {
                    "State": "associated"
                }
            }
        ],
        "IsDefault": False,
        "Tags": [
            {
                "Key": "Name",
                "Value": "Shared VPC"
            }
        ]
    },
]

DESCRIBE_FLOW_LOGS = [
    {
        "CreationTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
        "DeliverLogsPermissionArn": "arn:aws:iam::123456789012:role/flow-logs-role",
        "DeliverLogsStatus": "SUCCESS",
        "FlowLogId": "fl-aabbccdd112233445",
        "MaxAggregationInterval": 600,
        "FlowLogStatus": "ACTIVE",
        "LogGroupName": "FlowLogGroup",
        "ResourceId": "vpc-0e9801d129EXAMPLE",
        "TrafficType": "ALL",
        "LogDestinationType": "cloud-watch-logs",
        "LogFormat": "${version} ${account-id} ${interface-id} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${protocol} ${packets} ${bytes} ${start} ${end} ${action} ${log-status}"
    },
    {
        "CreationTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
        "DeliverLogsStatus": "SUCCESS",
        "FlowLogId": "fl-01234567890123456",
        "MaxAggregationInterval": 60,
        "FlowLogStatus": "ACTIVE",
        "ResourceId": "vpc-0e9801d129EXAMPLE",
        "TrafficType": "ACCEPT",
        "LogDestinationType": "s3",
        "LogDestination": "arn:aws:s3:::my-flow-log-bucket/custom",
        "LogFormat": "${version} ${vpc-id} ${subnet-id} ${instance-id} ${interface-id} ${account-id} ${type} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${pkt-srcaddr} ${pkt-dstaddr} ${protocol} ${bytes} ${packets} ${start} ${end} ${action} ${tcp-flags} ${log-status}"
    }
]