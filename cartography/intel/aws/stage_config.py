import typing
class AwsStageConfig:
    def __init__(
        self, boto3_session, current_aws_account_id, current_aws_account_regions, graph_job_parameters,
        permission_relationships_file, aws_accounts
    ):
        # TODO typehints
        self.boto3_session = boto3_session
        self.current_aws_account_id = current_aws_account_id
        self.current_aws_account_regions = current_aws_account_regions
        self.graph_job_parameters = graph_job_parameters
        self.permission_relationships_file = permission_relationships_file
        self.aws_accounts = aws_accounts
