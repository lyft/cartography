class Config:
    """
    A common interface for cartography configuration.

    All fields defined on this class must be present on a configuration object. Fields documented as required must
    contain valid values. Fields documented as optional may contain None, in which case cartography will choose a
    sensible default value for that piece of configuration.

    :type neo4j_uri: string
    :param neo4j_uri: URI for a Neo4j graph database service. Required.
    :type neo4j_user: string
    :param neo4j_user: User name for a Neo4j graph database service. Optional.
    :type neo4j_password: string
    :param neo4j_password: Password for a Neo4j graph database service. Optional.
    :type update_tag: int
    :param update_tag: Update tag for a cartography sync run. Optional.
    :type aws_sync_all_profiles: bool
    :param aws_sync_all_profiles: If True, AWS sync will run for all non-default profiles in the AWS_CONFIG_FILE. If
        False (default), AWS sync will run using the default credentials only. Optional.
    :type analysis_job_directory: str
    :param analysis_job_directory: Path to a directory tree containing analysis jobs to run. Optional.
    """

    def __init__(
        self,
        neo4j_uri,
        neo4j_user=None,
        neo4j_password=None,
        update_tag=None,
        aws_sync_all_profiles=False,
        analysis_job_directory=None,
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.update_tag = update_tag
        self.aws_sync_all_profiles = aws_sync_all_profiles
        self.analysis_job_directory = analysis_job_directory
