DESCRIBE_EVENTBUS_RESPONSE = [
    {
        "Arn": "arn:aws:cloudwatch:us-east-1:123456789012:eventbus/466df9e0-0dff-08e3-8e2f-5088487c4896",
        "Name": "string",
        "Policy": "string",
    },
]
DESCRIBE_LOG_GROUPS_RESPONSE = [
    {
        "storedBytes": 0,
        "metricFilterCount": 0,
        "creationTime": 1433189500783,
        "logGroupName": "my-logs",
        "retentionInDays": 5,
        "arn": "arn:aws:logs:us-west-2:0123456789012:log-group:my-logs:*",
        "kms": {
            "AWSAccountId": "846764612917",
            "KeyId": "b8a9477d-836c-491f-857e-07937918959b",
            "Arn": "arn:aws:kms:us-west-2:846764612917:key/b8a9477d-836c-491f-857e-07937918959b",
            "CreationDate": 1566518783.394,
            "Enabled": True,
            "Description": "Default KMS key that protects my S3 objects when no other key is defined",
            "KeyUsage": "ENCRYPT_DECRYPT",
            "KeyState": "Enabled",
            "Origin": "AWS_KMS",
            "KeyManager": "AWS",
            "CustomerMasterKeySpec": "SYMMETRIC_DEFAULT",
            "EncryptionAlgorithms": [
                "SYMMETRIC_DEFAULT",
            ],
        },
    },
]
DESCRIBE_METRICS_RESPONSE = [
    {
        "Namespace": "AWS/SNS",
        "Dimensions": [
            {
                "Name": "TopicName",
                "Value": "NotifyMe",
            },
        ],
        "MetricName": "PublishSize",
    },
]
DESCRIBE_EVENT_RULES_RESPONSE = [
    {
        "EventPattern": "{\"source\":[\"aws.autoscaling\"],\"detail-type\":[\"EC2 Instance Launch Successful\",\"EC2 Instance Terminate Successful\",\"EC2 Instance Launch Unsuccessful\",\"EC2 Instance Terminate Unsuccessful\"]}",
        "State": "DISABLED",
        "Name": "test",
        "Arn": "arn:aws:events:us-east-1:123456789012:rule/test",
        "Description": "Test rule for Auto Scaling events",
    },
]
