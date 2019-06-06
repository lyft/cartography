from collections import namedtuple

from cartography.intel.aws import iam


def test__find_roles_assumable_in_policy():
    Case = namedtuple('Case', ['message', 'statements', 'expected'])

    cases = (
        Case(
            'basic',
            [{
                "Action": "sts:AssumeRole",
                "Resource": "arn:aws:iam::000000000000:role/example-role-0",
                "Effect": "Allow",
            }],
            ["arn:aws:iam::000000000000:role/example-role-0"]
        ),
        Case(
            'must handle policies containing lists of statements',
            [
                {
                    "Action": "sts:AssumeRole",
                    "Resource": "arn:aws:iam::000000000000:role/example-role-0",
                    "Effect": "Allow",
                },
                {
                    "Action": "sts:AssumeRole",
                    "Resource": "arn:aws:iam::000000000000:role/example-role-1",
                    "Effect": "Allow",
                }
            ],
            [
                "arn:aws:iam::000000000000:role/example-role-0",
                "arn:aws:iam::000000000000:role/example-role-1",
            ]
        ),
        Case(
            'must handle statements containing lists of actions',
            [{
                "Action": ["sts:AssumeRole", "s3:GetObject"],
                "Resource": "arn:aws:iam::000000000000:role/example-role-0",
                "Effect": "Allow",
            }],
            ["arn:aws:iam::000000000000:role/example-role-0"]
        ),
        Case(
            'must handle actions containing wildcard characters',
            [{
                "Action": "*",
                "Resource": "arn:aws:iam::000000000000:role/example-role-0",
                "Effect": "Allow",
            }],
            ["arn:aws:iam::000000000000:role/example-role-0"]
        ),
        Case(
            'must not modify resource casing',
            [{
                "Action": "sts:AssumeRole",
                "Resource": "arn:aws:iam::000000000000:role/EXAMPLE-role-0",
                "Effect": "Allow",
            }],
            ["arn:aws:iam::000000000000:role/EXAMPLE-role-0"]
        ),
    )

    for case in cases:
        actual = iam._find_roles_assumable_in_policy(
            {
                "PolicyDocument": {
                    "Statement": case.statements,
                }
            }
        )
        assert actual == case.expected, case.message
