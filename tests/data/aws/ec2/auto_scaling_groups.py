import datetime
from datetime import timezone as tz


GET_LAUNCH_CONFIGURATIONS = [
    {
        'LaunchConfigurationName': 'example',
        'LaunchConfigurationARN': 'arn:aws:autoscaling:us-east-1:000000000000:launchConfiguration:00000000-0000-0000-0000-000000000000:launchConfigurationName/example',  # noqa:E501
        'ImageId': 'ami-00000000000000000',
        'KeyName': 'example-00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00',
        'SecurityGroups': [
            'sg-00000000000000000',
        ],
        'ClassicLinkVPCSecurityGroups': [],
        'UserData': '...',
        'InstanceType': 'r5.4xlarge',
        'KernelId': '',
        'RamdiskId': '',
        'BlockDeviceMappings': [
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': 200,
                    'VolumeType': 'gp2',
                    'DeleteOnTermination': True,
                },
            },
        ],
        'InstanceMonitoring': {
            'Enabled': False,
        },
        'IamInstanceProfile': 'example',
        'CreatedTime': datetime.datetime(2021, 9, 21, 10, 55, 34, 222000, tzinfo=tz.utc),
        'EbsOptimized': True,
    },
]
