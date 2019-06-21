class Config(object):
    """
    A common interface for drift-detection configuration.

    All fields defined on this class must be present on a configuration object. Fields documented as required must
    contain valid values. Fields documented as optional may contain None, in which case drift-detection will choose a
    sensible default value for that piece of configuration.

    :type neo4j_uri: string
    :param neo4j_uri: URI for a Neo4j graph database service. Required.
    :type neo4j_user: string
    :param neo4j_user: User name for a Neo4j graph database service. Optional.
    :type neo4j_password: string
    :param neo4j_password: Password for a Neo4j graph database service. Optional.
    :type drift_detector_directory: string
    :param drift_detector_directory: Path to a directory tree containing drift-detection detectors to run.
    :type update: bool
    :param update: If True, Drift-Detection will update each . Optional.
    """
    def __init__(self,
                 drift_detector_directory,
                 neo4j_uri,
                 neo4j_user=None,
                 neo4j_password=None,
                 update=False):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.drift_detector_directory = drift_detector_directory
        self.update = update
