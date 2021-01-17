from typing import Dict
from typing import List
from typing import Optional

import boto3.session
from typing_extensions import TypedDict

AwsGraphJobParameters = TypedDict('AwsGraphJobParameters', {'AWS_ID': str, 'UPDATE_TAG': int}, total=False)


class AwsStageConfig:
    def __init__(
        self,
        boto3_session: Optional[boto3.session.Session],
        current_aws_account_id: str,
        current_aws_account_regions: List[str],
        graph_job_parameters: AwsGraphJobParameters,
        permission_relationships_file: str,
        aws_accounts: Dict[str, str],
    ):
        self.boto3_session: boto3.Session = boto3_session
        self.current_aws_account_id: str = current_aws_account_id
        self.current_aws_account_regions: List[str] = current_aws_account_regions
        self.graph_job_parameters: AwsGraphJobParameters = graph_job_parameters
        self.permission_relationships_file: str = permission_relationships_file
        self.aws_accounts: Dict[str, str] = aws_accounts
