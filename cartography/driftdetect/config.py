class Config(object):
    """
    A common interface for drift-detection configuration.

    All fields defined on this class must be present on a configuration object. Fields documented as required must
    contain valid values. Fields documented as optional may contain None, in which case cartography will choose a
    sensible default value for that piece of configuration.

    :type neo4j_uri: string
    :param neo4j_uri: URI for a Neo4j graph database service. Required.
    :type neo4j_user: string
    :param neo4j_user: User name for a Neo4j graph database service. Optional.
    :type neo4j_password: string
    :param neo4j_password: Password for a Neo4j graph database service. Optional.
    :type drift_detection_directory:
    :param drift_detection_directory:
    :type start_state:
    :param start_state:
    :type end_state:
    :param end_state:
    """
    def __init__(self,
                 drift_detection_directory=None,
                 neo4j_uri=None,
                 neo4j_user=None,
                 neo4j_password=None,
                 start_state=None,
                 end_state=None):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.drift_detection_directory = drift_detection_directory
        self.start_state = start_state
        self.end_state = end_state
