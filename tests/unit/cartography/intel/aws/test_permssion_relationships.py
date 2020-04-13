from cartography.intel.aws import permission_relationships


GET_OBJECT_LOWERCASE_RESOURCE_WILDCARD = [
    {
        "action": [
            "s3:Get*",
        ],

        "resource": [
            "arn:aws:s3:::test*",
        ],
        "effect": "Allow",
    },
]


def test_admin_statments():
    statement = [{
        "action": [
            "*",
        ],

        "resource": [
            "*",
        ],
        "effect": "Allow",
    }]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_not_action_statement():
    statement = [{
        "action": [
            "*",
        ],
        "notaction":[
            "S3:GetObject",
        ],
        "resource": [
            "*",
        ],
        "effect": "Allow",
    }]
    assert (False, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_deny_statement():
    statement = [
        {
            "action": [
                "*",
            ],

            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
        {
            "action": [
                "S3:GetObject",
            ],

            "resource": [
                "*",
            ],
            "effect": "Deny",
        },
    ]
    assert (False, True) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_single_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],

            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_single_non_matching_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],

            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:PutObject"], "arn:aws:s3:::testbucket",
    )


def test_multiple_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],

            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject", "S3:PutObject", "S3:ListBuckets"], "arn:aws:s3:::testbucket",
    )


def test_multiple_non_matching_permission():
    statement = [
        {
            "action": [
                "S3:GetObject",
            ],

            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:PutObject", "S3:ListBuckets"], "arn:aws:s3:::testbucket",
    )


def test_single_permission_lower_case():
    statement = [
        {
            "action": [
                "s3:Get*",
            ],

            "resource": [
                "*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_single_permission_resource_allow():
    statement = [
        {
            "action": [
                "s3:Get*",
            ],

            "resource": [
                "arn:aws:s3:::test*",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_single_permission_resource_non_match():
    statement = [
        {
            "action": [
                "s3:Get*",
            ],

            "resource": [
                "arn:aws:s3:::nottest",
            ],
            "effect": "Allow",
        },
    ]
    assert (False, False) == permission_relationships.evaluate_policy_for_permission(
        statement, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_non_matching_notresource():
    statements = [
        {
            "action": [
                "s3:Get*",
            ],
            "resource":["*"],
            "notresource": [
                "arn:aws:s3:::nottest",
            ],
            "effect": "Allow",
        },
    ]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_no_action_statement():
    statements = [{
        "notaction": [
            "dynamodb:Query",
        ],
        "resource": [
            "*",
        ],
        "effect": "Allow",
    }]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_notaction_deny_without_allow():
    statements = [{
        "notaction": [
            "s3:*",
        ],
        "resource": [
            "*",
        ],
        "effect": "Allow",
    }]
    assert (False, False) == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_notaction_malformed():
    statements = [{
        "notaction": [
            "s3.*",
        ],
        "resource": [
            "*",
        ],
        "effect": "Allow",
    }]
    assert (True, False) == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_resource_substring():
    statements = [{
        "action": [
            "s3.*",
        ],
        "resource": [
            "arn:aws:s3:::test",
        ],
        "effect": "Allow",
    }]
    assert (False, False) == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket",
    )


def test_full_policy_explicit_deny():
    policies = {
        "fakeallow": [{
            "action": [
                "s3:*",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        }],
        "fakedeny": [{
            "action": [
                "s3:*",
            ],
            "resource": [
                "arn:aws:s3:::testbucket",
            ],
            "effect": "Deny",
        }],
    }
    assert not permission_relationships.evaluate_policies_against_resource(
        policies, "arn:aws:s3:::testbucket", ["S3:GetObject"],
    )


def test_full_policy_no_explicit_allow():
    policies = {
        "ListAllow": [{
            "action": [
                "s3:List*",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        }],
        "PutAllow": [{
            "action": [
                "s3:Put*",
            ],
            "resource": [
                "arn:aws:s3:::testbucket",
            ],
            "effect": "Allow",
        }],
    }
    assert not permission_relationships.evaluate_policies_against_resource(
        policies, "arn:aws:s3:::testbucket", ["S3:GetObject"],
    )


def test_full_policy_explicit_allow():
    policies = {
        "ListAllow": [{
            "action": [
                "s3:listobject"
                "dynamodb:query",
            ],
            "resource": [
                "*",
            ],
            "effect": "Allow",
        }],
        "explicitallow": [{
            "action": [
                "s3:getobject",
            ],
            "resource": [
                "arn:aws:s3:::testbucket",
            ],
            "effect": "Allow",
        }],
    }
    assert permission_relationships.evaluate_policies_against_resource(
        policies, "arn:aws:s3:::testbucket", ["S3:GetObject"],
    )


def test_full_multiple_principal():
    principals = {
        "test_principals1": {
            "ListAllow": [{
                "action": [
                    "s3:listobject"
                    "dynamodb:query",
                ],
                "resource": [
                    "*",
                ],
                "effect": "Allow",
            }],
            "explicitallow": [{
                "action": [
                    "s3:getobject",
                ],
                "resource": [
                    "arn:aws:s3:::testbucket",
                ],
                "effect": "Allow",
            }],
        },
        "test_principal2": {
            "ListAllow": [{
                "action": [
                    "s3:List*",
                ],
                "resource": [
                    "*",
                ],
                "effect": "Allow",
            }],
            "PutAllow": [{
                "action": [
                    "s3:Put*",
                ],
                "resource": [
                    "arn:aws:s3:::testbucket",
                ],
                "effect": "Allow",
            }],
        },
    }
    assert 1 == len(
        permission_relationships.evaluate_relationships(
            principals, ["arn:aws:s3:::testbucket"], ["S3:GetObject"],
        ),
    )
