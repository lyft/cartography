import datetime

from dateutil.tz import tzutc

GET_ELASTICBEANSTALK_APPLICATION = [
    {'ApplicationArn': 'arn:aws:elasticbeanstalk:us-east-1:000000000000:application/Scorekeep',
     'ApplicationName': 'Scorekeep',
     'ConfigurationTemplates': [],
     'DateCreated': datetime.datetime(2021, 11, 1, 1, 23, 6, 359000, tzinfo=tzutc()),
     'DateUpdated': datetime.datetime(2021, 11, 1, 1, 23, 6, 359000, tzinfo=tzutc()),
     'Description': 'RESTful web API in Java with Spring that provides an HTTP '
                    'interface for creating and managing game sessions and users.',
     'EnvironmentsList': [
         {'AbortableOperationInProgress': False,
          'ApplicationName': 'Scorekeep',
          'CNAME': 'BETA.jce-000000000000.us-east-1.elasticbeanstalk.com',
          'DateCreated': datetime.datetime(2021, 11, 1, 1, 23, 6, 359000, tzinfo=tzutc()),
          'DateUpdated': datetime.datetime(2021, 11, 1, 1, 23, 6, 359000, tzinfo=tzutc()),
          'EndpointURL': 'awseb-e-b-LJKFADFASD-341234123123-3123123124.us-east-1.elb.amazonaws.com',
          'EnvironmentArn': 'arn:aws:elasticbeanstalk:us-east-1:000000000000:environment/Scorekeep/BETA',
          'EnvironmentId': 'e-abcdefgh',
          'EnvironmentLinks': [],
          'EnvironmentName': 'BETA',
          'EnvironmentResources': {'AutoScalingGroups': [
              {'Name': 'awseb-e-fjlkdafsdkaf-stack-AWSEBAutoScalingGroup-LJKFJAS89DSF'}],
              'EnvironmentName': 'BETA',
              'Instances': [{'Id': 'i-jlkjfd7adfkasj2'}],
              'LaunchConfigurations': [{
                  'Name': 'awseb-e-jlkfsdflasd-stack-AWSEBAutoScalingLaunchConfiguration-KJhKJBJIkjh'}],
              'LaunchTemplates': [],
              'LoadBalancers': [{'Name': 'awseb-e-b-kjfasdUk-LKJF3JKHKBKHB2K1'}],
              'Queues': [],
              'Triggers': []},
          'Health': 'Grey',
          'HealthStatus': 'No Data',
          'PlatformArn': 'arn:aws:elasticbeanstalk:us-east-1::platform/Corretto '
                         '8 running on 32bit Amazon Linux '
                         '2/3.2.1',
          'SolutionStackName': '32bit Amazon Linux 2 v3.1.1 '
                               'running Corretto 8',
          'Status': 'Ready',
          'Tier': {'Name': 'WebServer',
                   'Type': 'Standard',
                   'Version': '1.0'},
          'VersionLabel': 'scorekeep-version-abcdefgh'}
     ],
     'ResourceLifecycleConfig': {
         'VersionLifecycleConfig': {
             'MaxAgeRule': {
                 'DeleteSourceFromS3': False,
                 'Enabled': False,
                 'MaxAgeInDays': 180
             },
             'MaxCountRule': {
                 'DeleteSourceFromS3': False,
                 'Enabled': False,
                 'MaxCount': 200
             }
         }
     },
     'Versions': ['scorekeep-version-abcdefgh'],
     'VersionsList': [
         {'ApplicationName': 'Scorekeep',
          'ApplicationVersionArn': 'arn:aws:elasticbeanstalk:us-east-1:000000000000:applicationversion/Scorekeep/scorekeep-version-abcdefgh',
          'DateCreated': datetime.datetime(2022, 12, 6, 7, 55, 21, 610000, tzinfo=tzutc()),
          'DateUpdated': datetime.datetime(2022, 12, 6, 7, 55, 21, 610000, tzinfo=tzutc()),
          'SourceBundle': {'S3Bucket': 'beanstalk-artifacts-jfksadjlffasdkf',
                           'S3Key': 'fjkldsjflaksdjflaksdjlasdk2312'},
          'Status': 'UNPROCESSED',
          'VersionLabel': 'scorekeep-version-abcdefgh'}
     ]
     }
]
