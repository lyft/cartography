from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import neo4j


def read_list_of_values_tx(tx: neo4j.Transaction, query: str, **kwargs) -> List[Union[str, int]]:
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    values = [n.value() for n in result]
    result.consume()
    return values


def read_single_value_tx(tx: neo4j.Transaction, query: str, **kwargs) -> Optional[Union[str, int]]:
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    record: neo4j.Record = result.single()

    value = record.value() if record else None

    result.consume()
    return value


def read_list_of_dicts_tx(tx: neo4j.Transaction, query: str, **kwargs) -> List[Dict[str, Any]]:
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    values = [n.data() for n in result]
    result.consume()
    return values


def read_list_of_tuples_tx(tx: neo4j.Transaction, query: str, **kwargs) -> List[Tuple[Any, ...]]:
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    values: List[Any] = result.values()
    result.consume()
    # All neo4j APIs return List type- https://neo4j.com/docs/api/python-driver/current/api.html#result - so we do this:
    return [tuple(val) for val in values]


def read_single_dict_tx(tx: neo4j.Transaction, query: str, **kwargs) -> Dict[str, Any]:
    result: neo4j.BoltStatementResult = tx.run(query, kwargs)
    record: neo4j.Record = result.single()

    value = record.data() if record else None

    result.consume()
    return value
