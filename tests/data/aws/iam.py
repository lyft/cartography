import datetime


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
                            "AWS": "arn:aws:iam::000000000000:root"
                        }
                    }
                ]
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000000",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-0",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-0"
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:role/example-role-0"
                        }
                    }
                ]
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000001",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-1",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-1"
        }
    ]
}
