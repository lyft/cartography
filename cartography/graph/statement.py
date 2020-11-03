import json
import logging

import backoff

logger = logging.getLogger(__name__)

# Attempt to run cleanup job for 10 minutes before giving up
CLEANUP_MAX_RETRY_TIME = 600


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


class GraphStatement:
    """
    A statement that will run against the cartography graph. Statements can query or update the graph.
    """

    def __init__(self, query, parameters=None, iterative=False, iterationsize=0):
        self.query = query
        self.parameters = parameters
        if not parameters:
            self.parameters = {}
        self.iterative = iterative
        self.iterationsize = iterationsize
        self.parameters["LIMIT_SIZE"] = self.iterationsize

    def merge_parameters(self, parameters):
        """
        Merge given parameters with existing parameters.
        """
        tmp = self.parameters.copy()
        tmp.update(parameters)
        self.parameters = tmp

    def run(self, session):
        """
        Run the statement. This will execute the query against the graph.
        """
        if self.iterative:
            self._run_iterative(session)
        else:
            self._run(session)

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

    def _run(self, session):
        """
        Non-iterative statement execution.
        """
        return session.run(self.query, self.parameters)

    def _run_iterative(self, session):
        """
        Runs the statement in batches of `LIMIT_SIZE` until `TotalCompleted` returns 0.
        This follows large delete transaction best practices in Neo4j:
        https://neo4j.com/developer/kb/large-delete-transaction-best-practices-in-neo4j/
        """
        self.parameters["LIMIT_SIZE"] = self.iterationsize
        self._run_iter_core(session)

    @backoff.on_predicate(backoff.fibo, max_time=CLEANUP_MAX_RETRY_TIME)
    def _run_iter_core(self, session):
        """
        Reruns the statement until TotalCompleted returns 0 using a backoff strategy and retry time limit.
        :return: None
        """
        total_completed = self._run(session).single()['TotalCompleted']
        return total_completed == 0

    @classmethod
    def create_from_json(cls, json_obj):
        """
        Create a statement from a JSON blob.
        """
        return cls(
            json_obj.get("query", ""),
            json_obj.get("parameters", {}),
            json_obj.get("iterative", False),
            json_obj.get("iterationsize", 0),
        )

    @classmethod
    def create_from_json_file(cls, file_path):
        """
        Create a statement from a JSON file.
        """
        with open(file_path) as json_file:
            data = json.load(json_file)

        return cls.create_from_json(data)
