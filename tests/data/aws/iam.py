import datetime


LIST_USERS = {
    "Users": [
        {
            "UserName": "example-user-0",
            "PasswordLastUsed": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "UserId": "AIDA00000000000000000",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:user/example-user-0",
        },
        {
            "UserName": "example-user-1",
            "PasswordLastUsed": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "UserId": "AIDA00000000000000001",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:user/example-user-1",
        },
    ],
}


LIST_GROUPS = {
    "Groups": [
        {
            "Path": "/",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "GroupId": "AGPA000000000000000000",
            "Arn": "arn:aws:iam::000000000000:group/example-group-0",
            "GroupName": "example-group-0",
        },
        {
            "Path": "/",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "GroupId": "AGPA000000000000000001",
            "Arn": "arn:aws:iam::000000000000:group/example-group-1",
            "GroupName": "example-group-1",
        },
    ],
}

INLINE_POLICY_STATEMENTS = [{
    "id": "allow_all_policy",
    "Action": [
        "*",
    ],
    "Resource": [
        "*",
    ],
    "Effect": "Allow",
}]

LIST_ROLES = {
    "Roles": [
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:root",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000000",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-0",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-0",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:role/example-role-0",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000001",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-1",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-1",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ec2.amazonaws.com",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000002",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-2",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-2",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRoleWithSAML",
                        "Effect": "Allow",
                        "Principal": {
                            "Federated": "arn:aws:iam::000000000000:saml-provider/ADFS",
                        },
                        "Condition": {
                            "StringEquals": {
                                "SAML:aud": "https://signin.aws.amazon.com/saml",
                            },
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000003",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-3",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-3",
        },
    ],
}

INSTANCE_PROFILE_ROLES = {
    'Roles': [
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:role/SERVICE_NAME_2",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000004",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "SERVICE_NAME_2",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/SERVICE_NAME_2",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000006",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "ANOTHER_SERVICE_NAME",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME",
        },
    ],
}

LIST_SERVER_CERTIFICATES = [
    {
        "Path": "/",
        "ServerCertificateName": "myUpdatedServerCertificate",
        "ServerCertificateId": "ASCAEXAMPLE123EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:server-certificate/myUpdatedServerCertificate",
        "UploadDate": datetime.datetime(2019, 4, 22, 21, 13, 44),
        "Expiration": datetime.datetime(2019, 10, 15, 22, 23, 16),
    },
    {
        "Path": "/cloudfront/",
        "ServerCertificateName": "MyTestCert",
        "ServerCertificateId": "ASCAEXAMPLE456EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:server-certificate/Org1/Org2/MyTestCert",
        "UploadDate": datetime.datetime(2015, 4, 21, 18, 14, 16),
        "Expiration": datetime.datetime(2018, 1, 14, 17, 52, 36),
    },
]

CREDENTIAL_REPORT_CONTENT = b'user,arn,user_creation_time,password_enabled,password_last_used,password_last_changed,password_next_rotation,mfa_active,access_key_1_active,access_key_1_last_rotated,access_key_1_last_used_date,access_key_1_last_used_region,access_key_1_last_used_service,access_key_2_active,access_key_2_last_rotated,access_key_2_last_used_date,access_key_2_last_used_region,access_key_2_last_used_service,cert_1_active,cert_1_last_rotated,cert_2_active,cert_2_last_rotated\n<root_account>,arn:aws:iam::000000000000:root,2022-03-23T10:21:07+00:00,not_supported,2022-08-26T15:26:38+00:00,not_supported,not_supported,false,false,N/A,N/A,N/A,N/A,false,N/A,N/A,N/A,N/A,false,N/A,false,N/A\nuser-cli,arn:aws:iam::000000000000:user/user1,2022-07-18T09:03:38+00:00,false,N/A,N/A,N/A,false,true,2022-08-01T13:51:50+00:00,2022-08-05T08:49:00+00:00,ap-northeast-3,glue,true,2022-08-29T08:39:55+00:00,2022-09-01T15:41:00+00:00,us-east-1,logs,false,N/A,false,N/A\nuser-readonly,arn:aws:iam::000000000000:user/user2,2022-08-31T11:10:33+00:00,false,2022-08-30T11:10:33+00:00,2022-08-31T11:10:33+00:00,2023-08-31T11:10:33+00:00,false,true,2022-08-31T11:10:34+00:00,2022-08-31T11:23:00+00:00,us-east-1,iam,true,2022-08-31T11:10:33+00:00,2022-08-31T11:10:33+00:00,N/A,N/A,false,2022-08-31T11:10:33+00:00,false,2022-08-31T11:10:33+00:00'  # noqa:E501

ACCOUNT_PASSWORD_POLICY = {
    'AllowUsersToChangePassword': False,
    'ExpirePasswords': False,
    'HardExpiry': False,
    'MaxPasswordAge': 90,
    'MinimumPasswordLength': 8,
    'PasswordReusePrevention': 12,
    'RequireLowercaseCharacters': False,
    'RequireNumbers': True,
    'RequireSymbols': True,
    'RequireUppercaseCharacters': False,
}

LIST_INSTANCE_PROFILES = {
    "InstanceProfiles": [
        {
            "InstanceProfileId": "AIPAIXEU4NUHUPEXAMPLE",
            "Roles": [
                {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Action": "sts:AssumeRole",
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": "arn:aws:iam::000000000000:role/SERVICE_NAME_2",
                                },
                            },
                        ],
                    },
                    "MaxSessionDuration": 3600,
                    "RoleId": "AROA00000000000000004",
                    "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
                    "RoleName": "SERVICE_NAME_2",
                    "Path": "/",
                    "Arn": "arn:aws:iam::000000000000:role/SERVICE_NAME_2",
                },
            ],
            "CreateDate": datetime.datetime(2013, 5, 11, 0, 2, 27),
            "InstanceProfileName": "ExampleInstanceProfile",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:instance-profile/SERVICE_NAME_2",
        },
        {
            "InstanceProfileId": "AIPAJVJVNRIQFREXAMPLE",
            "Roles": [],
            "CreateDate": datetime.datetime(2013, 6, 12, 23, 52, 2),
            "InstanceProfileName": "ExampleInstanceProfile2",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:instance-profile/PROFILE_NAME",
        },
        {
            "InstanceProfileId": "AIPAJVABCDEFFREXAMPLE",
            "Roles": [
                {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Action": "sts:AssumeRole",
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": "arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME",
                                },
                            },
                        ],
                    },
                    "MaxSessionDuration": 3600,
                    "RoleId": "AROA00000000000000006",
                    "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
                    "RoleName": "ANOTHER_SERVICE_NAME",
                    "Path": "/",
                    "Arn": "arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME",
                },
            ],
            "CreateDate": datetime.datetime(2013, 6, 12, 23, 52, 2),
            "InstanceProfileName": "ExampleInstanceProfile3",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:instance-profile/ANOTHER_SERVICE_NAME",
        },
    ],
}
