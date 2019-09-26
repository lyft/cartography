import json
import logging

from cartography.graph.statement import GraphStatement

logger = logging.getLogger(__name__)


class GraphJobJSONEncoder(json.JSONEncoder):
    """
    Support JSON serialization for GraphJob instances.
    """

    def default(self, obj):
        if isinstance(obj, GraphJob):
            return obj.as_dict()
        else:
            # Let the default encoder roll up the exception.
            return json.JSONEncoder.default(self, obj)


class GraphJob:
    """
    A job that will run against the cartography graph. A job is a sequence of statements which execute sequentially.
    """

    def __init__(self, name, statements):
        self.name = name
        self.statements = statements

    def merge_parameters(self, parameters):
        """
        Merge parameters for all job statements.
        """
        for s in self.statements:
            s.merge_parameters(parameters)

    def run(self, neo4j_session):
        """
        Run the job. This will execute all statements sequentially.
        """
        logger.debug("Starting job '%s'.", self.name)
        for stm in self.statements:
            try:
                stm.run(neo4j_session)
            except Exception as e:
                logger.error(
                    "Unhandled error while executing statement in job '%s': %s",
                    self.name,
                    e,
                )
                raise
        logger.debug("Finished job '%s'.", self.name)

    def as_dict(self):
        """
        Convert job to a dictionary.
        """
        return {
            "name": self.name,
            "statements": [s.as_dict() for s in self.statements],
        }

    @classmethod
    def from_json(cls, blob):
        """
        Create a job from a JSON blob.
        """
        data = json.loads(blob)
        statements = _get_statements_from_json(data)
        name = data["name"]
        return cls(name, statements)

    @classmethod
    def from_json_file(cls, file_path):
        """
        Create a job from a JSON file.
        """
        with open(file_path) as j_file:
            data = json.load(j_file)
        statements = _get_statements_from_json(data)
        name = data["name"]
        return cls(name, statements)

    @classmethod
    def run_from_json(cls, neo4j_session, blob, parameters=None):
        """
        Run a job from a JSON blob. This will deserialize the job and execute all statements sequentially.
        """
        if not parameters:
            parameters = {}

        job = cls.from_json(blob)
        job.merge_parameters(parameters)
        job.run(neo4j_session)

    @classmethod
    def run_from_json_file(cls, file_path, neo4j_session, parameters=None):
        """
        Run a job from a JSON file. This will deserialize the job and execute all statements sequentially.
        """
        if not parameters:
            parameters = {}

        job = cls.from_json_file(file_path)
        job.merge_parameters(parameters)
        job.run(neo4j_session)


def _get_statements_from_json(blob):
    """
    Deserialize all statements from the JSON blob.
    """
    statements = []
    for statement_data in blob["statements"]:
        statement = GraphStatement.create_from_json(statement_data)
        statements.append(statement)

    return statements
