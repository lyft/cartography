from collections import namedtuple

from cartography.intel.aws import permission_relationships

ADMIN_STATEMENTS = [{
    "action": [
        "*"
    ],

    "resource": [
        "*"
    ],
    "effect": "Allow"
}]

S3_GET_NOTACTION = [{
    "action": [
        "*"
    ],
    "notaction":[
        "S3:GetObject"
    ],
    "resource": [
        "*"
    ],
    "effect": "Allow"
}]

ADMIN_S3_DENY = [{
    "action": [
        "*"
    ],

    "resource": [
        "*"
    ],
    "effect": "Allow"
},
    {
    "action": [
        "S3:GetObject"
    ],

    "resource": [
        "*"
    ],
    "effect": "Deny"
}]

GET_OBJECT_ONLY = [
    {
        "action": [
            "S3:GetObject"
        ],

        "resource": [
            "*"
        ],
        "effect": "Allow"
    }
]

GET_OBJECT_LOWERCASE = [
    {
        "action": [
            "s3:Get*"
        ],

        "resource": [
            "*"
        ],
        "effect": "Allow"
    }
]

GET_OBJECT_LOWERCASE_RESOURCE_WILDCARD = [
    {
        "action": [
            "s3:Get*"
        ],

        "resource": [
            "arn:aws:s3:::test*"
        ],
        "effect": "Allow"
    }
]

GET_OBJECT_LOWERCASE_RESOURCE_NOT_ALLOW = [
    {
        "action": [
            "s3:Get*"
        ],

        "resource": [
            "arn:aws:s3:::nottest"
        ],
        "effect": "Allow"
    }
]


def test_admin_statments():
    assert True == permission_relationships.evaluate_policy_for_permission(
        ADMIN_STATEMENTS, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_not_action_statement():
    assert False == permission_relationships.evaluate_policy_for_permission(
        S3_GET_NOTACTION, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_deny_statement():
    assert False == permission_relationships.evaluate_policy_for_permission(
        ADMIN_S3_DENY, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_single_permission():
    assert True == permission_relationships.evaluate_policy_for_permission(
        GET_OBJECT_ONLY, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_single_non_matching_permission():
    assert False == permission_relationships.evaluate_policy_for_permission(
        GET_OBJECT_ONLY, ["S3:PutObject"], "arn:aws:s3:::testbucket")


def test_multiple_permission():
    assert True == permission_relationships.evaluate_policy_for_permission(
        GET_OBJECT_ONLY, ["S3:GetObject", "S3:PutObject", "S3:ListBuckets"], "arn:aws:s3:::testbucket")


def test_multiple_non_matching_permission():
    assert False == permission_relationships.evaluate_policy_for_permission(
        GET_OBJECT_ONLY, ["S3:PutObject", "S3:ListBuckets"], "arn:aws:s3:::testbucket")


def test_single_permission_lower_case():
    assert True == permission_relationships.evaluate_policy_for_permission(
        GET_OBJECT_LOWERCASE, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_single_permission_resource_allow():
    assert True == permission_relationships.evaluate_policy_for_permission(
        GET_OBJECT_LOWERCASE_RESOURCE_WILDCARD, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_single_permission_resource_non_match():
    assert False == permission_relationships.evaluate_policy_for_permission(
        GET_OBJECT_LOWERCASE_RESOURCE_NOT_ALLOW, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_non_matching_notresource():
    statements = [
        {
            "action": [
                "s3:Get*"
            ],
            "resource":["*"],
            "notresource": [
                "arn:aws:s3:::nottest"
            ],
            "effect": "Allow"
        }
    ]
    assert True == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket")


def test_no_action_statement():
    statements = [{
        "notaction":[
            "dynamodb:Query"
        ],
        "resource": [
            "*"
        ],
        "effect": "Allow"
    }]
    assert True == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket")

def test_notaction_deny_without_allow():
    statements = [{
        "notaction":[
            "s3.*"
        ],
        "resource": [
            "*"
        ],
        "effect": "Allow"
    }]
    assert False == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket")

def test_resource_substring():
    statements = [{
        "action":[
            "s3.*"
        ],
        "resource": [
            "arn:aws:s3:::test"
        ],
        "effect": "Allow"
    }]
    assert False == permission_relationships.evaluate_policy_for_permission(
        statements, ["S3:GetObject"], "arn:aws:s3:::testbucket")
