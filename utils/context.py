
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
        inventory_sync_request_topic=None,
        inventory_sync_result_topic=None,
        inventory_sync_offline_url=None,
        iam_deepdive_request_topic=None,
        iam_deepdive_result_topic=None,
        iam_deepdive_offline_url=None,
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
        self.inventory_sync_request_topic = inventory_sync_request_topic
        self.inventory_sync_result_topic = inventory_sync_result_topic
        self.inventory_sync_offline_url = inventory_sync_offline_url
        self.iam_deepdive_request_topic = iam_deepdive_request_topic
        self.iam_deepdive_result_topic = iam_deepdive_result_topic
        self.iam_deepdive_offline_url = iam_deepdive_offline_url
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_pwd = neo4j_pwd

    def parse_config(self, config):
        self.authorization_key = config['authorization']['key']
        self.authorization_value = config['authorization']['value']
        self.assume_role_access_key_cipher = config['kms']['assumeRoleAccessKeyCipher']
        self.assume_role_access_secret_cipher = config['kms']['assumeRoleAccessSecretCipher']
        self.inventory_sync_request_topic = config['inventorysyncaws']['sns']['requestTopic']
        self.inventory_sync_result_topic = config['inventorysyncaws']['sns']['resultTopic']
        self.inventory_sync_offline_url = config['inventorysyncaws']['sns'].get('offlineURL')
        self.iam_deepdive_request_topic = config['awsiamdeepdive']['sns']['requestTopic']
        self.iam_deepdive_result_topic = config['awsiamdeepdive']['sns']['resultTopic']
        self.iam_deepdive_offline_url = config['awsiamdeepdive']['sns'].get('offlineURL')
        self.neo4j_uri = config['neo4j']['uri']
        self.neo4j_user = config['neo4j']['user']
        self.neo4j_pwd = config['neo4j']['pwd']
