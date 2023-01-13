CLOUD_WATCH_ALARMS = [
    {
        'AlarmName': 'alarmName1',
        'AlarmArn': 'alarmArn1',
        'MetricName': 'metricName1',
    },
    {
        'AlarmName': 'alarmName2',
        'AlarmArn': 'alarmArn2',
        'MetricName': 'metricName2',
    },
]

CLOUD_WATCH_LOG_GROUPS = [
    {
        'logGroupName': 'logGroupName1',
        'creationTime': 1672009127911,
        'retentionInDays': 30,
        'metricFilterCount': 2,
        'arn': 'arn:aws:logs:us-east-1:000000000000:log-group:logGroupName1:*',
        'storedBytes': 123,
        'dataProtectionStatus': 'ACTIVATED',
    },
    {
        'logGroupName': 'logGroupName2',
        'creationTime': 1672009127911,
        'retentionInDays': 1,
        'metricFilterCount': 1,
        'arn': 'arn:aws:logs:us-east-1:000000000000:log-group:logGroupName2:*',
        'storedBytes': 123,
        'kmsKeyId': 'kmsKeyId',
        'dataProtectionStatus': 'DISABLED',
    },
]

CLOUD_WATCH_METRIC_FILTERS = [
    {
        'filterName': 'filterName1',
        'filterPattern': 'filterPattern1',
        'metricTransformations': [
            {
                'metricName': 'metricName1',
            },
        ],
        'creationTime': 1672009127918,
        'logGroupName': 'logGroupName1',
    },
    {
        'filterName': 'filterName2',
        'filterPattern': 'filterPattern2',
        'metricTransformations': [
            {
                'metricName': 'metricName2',
            },
        ],
        'creationTime': 1672009127920,
        'logGroupName': 'logGroupName2',
    },
]
