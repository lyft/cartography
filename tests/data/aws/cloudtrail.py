import datetime
from datetime import timezone as tz

CLOUDTRAIL_TRAILS = [
    {
        "Name": "Name",
        "S3BucketName": "S3BucketName",
        "S3KeyPrefix": "S3KeyPrefix",
        "SnsTopicName": "SnsTopicName",
        "SnsTopicARN": "SnsTopicARN",
        "IncludeGlobalServiceEvents": True,
        "IsMultiRegionTrail": True,
        "HomeRegion": "HomeRegion",
        "TrailARN": "arn:aws:cloudtrail:us-east-1:000000000000:trail/TRAIL1",
        "LogFileValidationEnabled": True,
        "CloudWatchLogsLogGroupArn": "CloudWatchLogsLogGroupArn",
        "CloudWatchLogsRoleArn": "CloudWatchLogsRoleArn",
        "KmsKeyId": "KmsKeyId",
        "HasCustomEventSelectors": True,
        "HasInsightSelectors": True,
        "IsOrganizationTrail": True,
        "IsLogging": False,
    },
    {
        "Name": "Name",
        "S3BucketName": "S3BucketName",
        "S3KeyPrefix": "S3KeyPrefix",
        "SnsTopicName": "SnsTopicName",
        "SnsTopicARN": "SnsTopicARN",
        "IncludeGlobalServiceEvents": False,
        "IsMultiRegionTrail": False,
        "HomeRegion": "HomeRegion",
        "TrailARN": "arn:aws:cloudtrail:us-east-1:000000000001:trail/TRAIL2",
        "LogFileValidationEnabled": True,
        "CloudWatchLogsLogGroupArn": "CloudWatchLogsLogGroupArn",
        "LatestCloudWatchLogsDeliveryTime": datetime.datetime(2021, 10, 12, 12, 19, 6, 294000, tzinfo=tz.utc),
        "CloudWatchLogsRoleArn": "CloudWatchLogsRoleArn",
        "KmsKeyId": "KmsKeyId",
        "HasCustomEventSelectors": True,
        "HasInsightSelectors": False,
        "IsOrganizationTrail": False,
        "IsLogging": True,
    },
]

TRAIL_ARN_TO_CLOUDTRAIL_EVENT_SELECTORS = {
    "arn:aws:cloudtrail:us-east-1:000000000000:trail/TRAIL1": [
        {
            'ReadWriteType': 'All',
            'IncludeManagementEvents': True,
        },
        {
            'ReadWriteType': 'WriteOnly',
            'IncludeManagementEvents': False,
            'DataResources': [
                {
                    'Type': 'AWS::S3::Object',
                    'Values': [
                        'arn:aws:s3:::bucket-1/',
                    ],
                },
                {
                    'Type': 'AWS::S3::Object',
                    'Values': [
                        'arn:aws:s3:::bucket-2/',
                    ],
                },
            ],
            'ExcludeManagementEventSources': [],
        },
    ],
    "arn:aws:cloudtrail:us-east-1:000000000001:trail/TRAIL2": [
        {
            'ReadWriteType': 'All',
            'IncludeManagementEvents': True,
            'DataResources': [],
            'ExcludeManagementEventSources': ["kms.amazonaws.com"],
        },
    ],
}
