
class AppContext:
    def __init__(
        self,
        region=None,
        log_level=None,
        app_env=None,
        config_kms_key_id=None,
        config=None,
        logger=None,
        authorization_key=None,
        authorization_value=None,
        assume_role_access_key_cipher=None,
        assume_role_access_secret_cipher=None,
        aws_inventory_sync_request_topic=None,
        aws_inventory_sync_result_topic=None,
        aws_inventory_sync_offline_url=None,
        aws_iam_deepdive_request_topic=None,
        aws_iam_deepdive_result_topic=None,
        aws_iam_deepdive_offline_url=None,
        aws_inventory_views_request_topic=None,
        aws_inventory_views_result_topic=None,
        aws_inventory_views_offline_url=None,
        aws_audit_request_topic=None,
        aws_audit_result_topic=None,
        aws_audit_offline_url=None,
        neo4j_uri=None,
        neo4j_user=None,
        neo4j_pwd=None
    ):
        self.region = region
        self.log_level = log_level
        self.app_env = app_env
        self.config_kms_key_id = config_kms_key_id
        self.config = config
        self.logger = logger
        self.authorization_key = authorization_key
        self.authorization_value = authorization_value
        self.assume_role_access_key_cipher = assume_role_access_key_cipher
        self.assume_role_access_secret_cipher = assume_role_access_secret_cipher
        self.aws_inventory_sync_request_topic = aws_inventory_sync_request_topic
        self.aws_inventory_sync_result_topic = aws_inventory_sync_result_topic
        self.aws_inventory_sync_offline_url = aws_inventory_sync_offline_url
        self.aws_iam_deepdive_request_topic = aws_iam_deepdive_request_topic
        self.aws_iam_deepdive_result_topic = aws_iam_deepdive_result_topic
        self.aws_iam_deepdive_offline_url = aws_iam_deepdive_offline_url
        self.aws_inventory_views_request_topic = aws_inventory_views_request_topic
        self.aws_inventory_views_result_topic = aws_inventory_views_result_topic
        self.aws_inventory_views_offline_url = aws_inventory_views_offline_url
        self.aws_audit_request_topic = aws_audit_request_topic
        self.aws_audit_result_topic = aws_audit_result_topic
        self.aws_audit_offline_url = aws_audit_offline_url
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_pwd = neo4j_pwd

    def parse_config(self, config):
        self.authorization_key = config['authorization']['key']
        self.authorization_value = config['authorization']['value']
        self.assume_role_access_key_cipher = config['kms']['assumeRoleAccessKeyCipher']
        self.assume_role_access_secret_cipher = config['kms']['assumeRoleAccessSecretCipher']
        self.aws_inventory_sync_request_topic = config['awsinventorysync']['sns']['requestTopic']
        self.aws_inventory_sync_result_topic = config['awsinventorysync']['sns']['resultTopic']
        self.aws_inventory_sync_offline_url = config['awsinventorysync']['sns'].get('offlineURL')
        self.aws_iam_deepdive_request_topic = config['awsiamdeepdive']['sns']['requestTopic']
        self.aws_iam_deepdive_result_topic = config['awsiamdeepdive']['sns']['resultTopic']
        self.aws_iam_deepdive_offline_url = config['awsiamdeepdive']['sns'].get('offlineURL')
        self.aws_inventory_views_request_topic = config['awsinventoryviews']['sns']['requestTopic']
        self.aws_inventory_views_result_topic = config['awsinventoryviews']['sns']['resultTopic']
        self.aws_inventory_views_offline_url = config['awsinventoryviews']['sns'].get('offlineURL')
        self.aws_audit_request_topic = config['awsaudit']['sns']['requestTopic']
        self.aws_audit_result_topic = config['awsaudit']['sns']['resultTopic']
        self.aws_audit_offline_url = config['awsaudit']['sns'].get('offlineURL')
        self.neo4j_uri = config['neo4j']['uri']
        self.neo4j_user = config['neo4j']['user']
        self.neo4j_pwd = config['neo4j']['pwd']
