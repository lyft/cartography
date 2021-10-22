import json
import logging
import os
from pathlib import Path
from typing import Dict
from typing import Union

import neo4j

from cartography.stats import get_stats_client


logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


class GraphStatementJSONEncoder(json.JSONEncoder):
    """
    Support JSON serialization for GraphStatement instances.
    """

    def default(self, obj):
        if isinstance(obj, GraphStatement):
            return obj.as_dict()
        else:
            # Let the default encoder roll up the exception.
            return json.JSONEncoder.default(self, obj)


# TODO move this cartography.util after we move util.run_*_job to cartography.graph.job.
def get_job_shortname(file_path: Union[Path, str]) -> str:
    # Return filename without path and extension
    return os.path.splitext(file_path)[0]


class GraphStatement:
    """
    A statement that will run against the cartography graph. Statements can query or update the graph.
    """

    def __init__(
        self, query: str, parameters: Dict = None, iterative: bool = False, iterationsize: int = 0,
        parent_job_name: str = None, parent_job_sequence_num: int = None,
    ):
        self.query = query
        self.parameters: Dict = parameters
        if not parameters:
            self.parameters = {}
        self.iterative = iterative
        self.iterationsize = iterationsize
        self.parameters["LIMIT_SIZE"] = self.iterationsize

        self.parent_job_name = parent_job_name if parent_job_name else None
        self.parent_job_sequence_num = parent_job_sequence_num if parent_job_sequence_num else None

    def merge_parameters(self, parameters):
        """
        Merge given parameters with existing parameters.
        """
        tmp = self.parameters.copy()
        tmp.update(parameters)
        self.parameters = tmp

    def run(self, session: neo4j.Session) -> None:
        """
        Run the statement. This will execute the query against the graph.
        """
        if self.iterative:
            self._run_iterative(session)
        else:
            session.write_transaction(self._run_noniterative).consume()
        logger.info(f"Completed {self.parent_job_name} statement #{self.parent_job_sequence_num}")

    def as_dict(self):
        """
        Convert statement to a dictionary.
        """
        return {
            "query": self.query,
            "parameters": self.parameters,
            "iterative": self.iterative,
            "iterationsize": self.iterationsize,
        }

    def _run_noniterative(self, tx: neo4j.Transaction) -> neo4j.StatementResult:
        """
        Non-iterative statement execution.
        """
        result: neo4j.StatementResult = tx.run(self.query, self.parameters)

        # Handle stats
        summary: neo4j.BoltStatementResultSummary = result.summary()
        objects_changed: int = (
            summary.counters.constraints_added +
            summary.counters.constraints_removed +
            summary.counters.indexes_added +
            summary.counters.indexes_removed +
            summary.counters.labels_added +
            summary.counters.labels_removed +
            summary.counters.nodes_created +
            summary.counters.nodes_deleted +
            summary.counters.properties_set +
            summary.counters.relationships_created +
            summary.counters.relationships_deleted
        )
        stat_handler.incr(f'{self.parent_job_name}-{self.parent_job_sequence_num}-objects_changed', objects_changed)

        return result

    def _run_iterative(self, session: neo4j.Session) -> None:
        """
        Iterative statement execution.

        Expects the query to return the total number of records updated.
        """
        self.parameters["LIMIT_SIZE"] = self.iterationsize

        while True:
            result: neo4j.StatementResult = session.write_transaction(self._run_noniterative)

            # Exit if we have finished processing all items
            if not result.summary().counters.contains_updates:
                # Ensure network buffers are cleared
                result.consume()
                break
            result.consume()

    @classmethod
    def create_from_json(cls, json_obj: Dict, short_job_name: str = None, job_sequence_num: int = None):
        """
        Create a statement from a JSON blob.
        """
        return cls(
            json_obj.get("query", ""),
            json_obj.get("parameters", {}),
            json_obj.get("iterative", False),
            json_obj.get("iterationsize", 0),
            short_job_name,
            job_sequence_num,
        )

    @classmethod
    def create_from_json_file(cls, file_path: Path):
        """
        Create a statement from a JSON file.
        """
        with open(file_path) as json_file:
            data = json.load(json_file)

        return cls.create_from_json(data, get_job_shortname(file_path))
