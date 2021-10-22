import json
import logging
from pathlib import Path
from typing import Dict
from typing import List

import neo4j

from cartography.graph.statement import get_job_shortname
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

    def __init__(self, name: str, statements: List[GraphStatement], short_name: str = None):
        # E.g. "Okta intel module cleanup"
        self.name = name
        self.statements: List[GraphStatement] = statements
        # E.g. "okta_import_cleanup"
        self.short_name = short_name

    def merge_parameters(self, parameters: Dict) -> None:
        """
        Merge parameters for all job statements.
        """
        for s in self.statements:
            s.merge_parameters(parameters)

    def run(self, neo4j_session: neo4j.Session):
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
        log_msg = f"Finished job {self.short_name}" if self.short_name else f"Finished job {self.name}"
        logger.info(log_msg)

    def as_dict(self) -> Dict:
        """
        Convert job to a dictionary.
        """
        return {
            "name": self.name,
            "statements": [s.as_dict() for s in self.statements],
            "short_name": self.short_name,
        }

    @classmethod
    def from_json(cls, blob: str, short_name: str = None):
        """
        Create a job from a JSON blob.
        """
        data: Dict = json.loads(blob)
        statements = _get_statements_from_json(data, short_name)
        name = data["name"]
        return cls(name, statements, short_name)

    @classmethod
    def from_json_file(cls, file_path: Path):
        """
        Create a job from a JSON file.
        """
        with open(file_path) as j_file:
            data: Dict = json.load(j_file)

        job_shortname: str = get_job_shortname(file_path)
        statements: List[GraphStatement] = _get_statements_from_json(data, job_shortname)
        name: str = data["name"]
        return cls(name, statements, job_shortname)

    @classmethod
    def run_from_json(
        cls, neo4j_session: neo4j.Session, blob: str, parameters: Dict = None, short_name: str = None,
    ) -> None:
        """
        Run a job from a JSON blob. This will deserialize the job and execute all statements sequentially.
        """
        if not parameters:
            parameters = {}

        job: GraphJob = cls.from_json(blob, short_name)
        job.merge_parameters(parameters)
        job.run(neo4j_session)

    @classmethod
    def run_from_json_file(cls, file_path: Path, neo4j_session: neo4j.Session, parameters: Dict = None) -> None:
        """
        Run a job from a JSON file. This will deserialize the job and execute all statements sequentially.
        """
        if not parameters:
            parameters = {}

        job: GraphJob = cls.from_json_file(file_path)

        job.merge_parameters(parameters)
        job.run(neo4j_session)


def _get_statements_from_json(blob: Dict, short_job_name: str = None) -> List[GraphStatement]:
    """
    Deserialize all statements from the JSON blob.
    """
    statements: List[GraphStatement] = []
    for i, statement_data in enumerate(blob["statements"]):
        # i+1 to make it 1-based and not 0-based to help with log readability
        statement: GraphStatement = GraphStatement.create_from_json(statement_data, short_job_name, i + 1)
        statements.append(statement)

    return statements
