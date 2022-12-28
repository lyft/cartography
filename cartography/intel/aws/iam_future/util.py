import enum
from typing import Any
from typing import List


class PolicyType(enum.Enum):
    managed = 'managed'
    inline = 'inline'


def create_policy_id(principal_arn: str, policy_type: str, name: str) -> str:
    return f"{principal_arn}/{policy_type}_policy/{name}"


def create_policy_statement_id(policy_id: str, statement_sid: str) -> str:
    return f"{policy_id}/statement/{statement_sid}"


def ensure_list(obj: Any) -> List[Any]:
    if not isinstance(obj, list):
        obj = [obj]
    return obj
