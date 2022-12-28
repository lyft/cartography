import enum


class PolicyType(enum.Enum):
    managed = 'managed'
    inline = 'inline'


def create_policy_id(principal_arn: str, policy_type: str, name: str) -> str:
    return f"{principal_arn}/{policy_type}_policy/{name}"
