from datetime import datetime

from dateutil.tz import tzutc


GET_USER_LIST_DATA = {
    'Users': [
        {
            'Path': '/',
            'UserName': 'user1',
            'UserId': 'AIDAXJNIGTSXXX',
            'Arn': 'arn:aws:iam::1234:user/user1',
            'CreateDate': datetime(2022, 7, 27, 20, 24, 23, tzinfo=tzutc()),
        },
        {
            'Path': '/',
            'UserName': 'user2',
            'UserId': 'AIDAXJNIGTSXXY',
            'Arn': 'arn:aws:iam::1234:user/user2',
            'CreateDate': datetime(2021, 1, 25, 18, 8, 53, tzinfo=tzutc()),
        },
        {
            'Path': '/',
            'UserName': 'user3',
            'UserId': 'AIDAXJNIGTSQXYY',
            'Arn': 'arn:aws:iam::1234:user/user3',
            'CreateDate': datetime(2020, 3, 23, 20, 26, 23, tzinfo=tzutc()),
        },
    ],
}


GET_USER_MANAGED_POLS_SAMPLE = {
    'arn:aws:iam::1234:user/user1': {
        'arn:aws:iam::1234:policy/user1-user-policy': [
            {
                'Sid': 'VisualEditor0',
                'Effect': 'Allow',
                'Action': ['iam:DeleteRolePolicy', 'iam:CreateRole', 'iam:PutRolePolicy'],
                'Resource': '*',
            },
            {
                'Sid': 'VisualEditor1',
                'Effect': 'Allow',
                'Action': 'iam:PutRolePolicy',
                'Resource': 'arn:aws:iam::1234:role/lambda-user1-exec',
            },
        ],
        'arn:aws:iam::aws:policy/AmazonS3FullAccess': [{
            'Effect': 'Allow',
            'Action': ['s3:*', 's3-object-lambda:*'],
            'Resource': '*',
        }],
        'arn:aws:iam::aws:policy/AWSLambda_FullAccess': [
            {
                'Effect': 'Allow',
                'Action': [
                    'cloudformation:DescribeStacks',
                    'cloudformation:ListStackResources',
                    'cloudwatch:ListMetrics',
                    'cloudwatch:GetMetricData',
                    'ec2:DescribeSecurityGroups',
                    'ec2:DescribeSubnets',
                    'ec2:DescribeVpcs',
                    'kms:ListAliases',
                    'iam:GetPolicy',
                    'iam:GetPolicyVersion',
                    'iam:GetRole',
                    'iam:GetRolePolicy',
                    'iam:ListAttachedRolePolicies',
                    'iam:ListRolePolicies',
                    'iam:ListRoles',
                    'lambda:*',
                    'logs:DescribeLogGroups',
                    'states:DescribeStateMachine',
                    'states:ListStateMachines',
                    'tag:GetResources',
                    'xray:GetTraceSummaries',
                    'xray:BatchGetTraces',
                ],
                'Resource': '*',
            },
            {
                'Effect': 'Allow',
                'Action': 'iam:PassRole',
                'Resource': '*',
                'Condition': {'StringEquals': {'iam:PassedToService': 'lambda.amazonaws.com'}},
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'logs:DescribeLogStreams',
                    'logs:GetLogEvents',
                    'logs:FilterLogEvents',
                ],
                'Resource': 'arn:aws:logs:*:*:log-group:/aws/lambda/*',
            },
        ],
    },
    'arn:aws:iam::1234:user/user2': {},
    'arn:aws:iam::1234:user/user3': {
        'arn:aws:iam::aws:policy/AdministratorAccess': [{
            'Effect': 'Allow',
            'Action': '*',
            'Resource': '*',
        }],
    },
}
