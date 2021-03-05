import json
import logging

import neo4j

logger = logging.getLogger(__name__)


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

    def run(self, session) -> None:
        """
        Run the statement. This will execute the query against the graph.
        """
        tx: neo4j.Transaction = session.begin_transaction()
        if self.iterative:
            self._run_iterative(tx)
        else:
            data: neo4j.StatementResult = self._run(tx)
            data.consume()
        tx.commit()

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

    def _run(self, tx: neo4j.Transaction) -> neo4j.StatementResult:
        """
        Non-iterative statement execution.
        """
        return tx.run(self.query, self.parameters)

    def _run_iterative(self, tx: neo4j.Transaction) -> None:
        """
        Iterative statement execution.

        Expects the query to return the total number of records updated.
        """
        self.parameters["LIMIT_SIZE"] = self.iterationsize

        while True:
            result: neo4j.StatementResult = self._run(tx)
            record: neo4j.Record = result.single()

            # TODO: use the BoltStatementResultSummary object to determine the number of items processed
            total_completed = int(record['TotalCompleted'])
            logger.debug("Processed %d items", total_completed)

            # Ensure network buffers are cleared
            result.consume()
            if total_completed == 0:
                break

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
