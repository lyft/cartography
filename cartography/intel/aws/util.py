from typing import Dict
from typing import List

import boto3.session
from typing_extensions import TypedDict

GraphJobParameters = TypedDict('GraphJobParameters', {'AWS_ID': str, 'UPDATE_TAG': int}, total=False)


class AwsStageConfig:
    def __init__(
        self,
        boto3_session: boto3.session.Session,
        current_aws_account_id: str,
        current_aws_account_regions: List[str],
        graph_job_parameters: GraphJobParameters,
        permission_relationships_file: str,
        aws_accounts: Dict[str, str],
    ):
        self.boto3_session = boto3_session
        self.current_aws_account_id = current_aws_account_id
        self.current_aws_account_regions = current_aws_account_regions
        self.graph_job_parameters = graph_job_parameters
        self.permission_relationships_file = permission_relationships_file
        self.aws_accounts = aws_accounts
