from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import read_single_dict_tx
from cartography.client.core.tx import read_single_value_tx


def _ensure_test_data(neo4j_session):
    neo4j_session.run("""
            MERGE (t:TestNode{name: "Homer", age: 39})
            MERGE (t:TestNode{name: "Lisa", age: 8})
            MERGE (t:TestNode{name: "Marge", age: 36})
        """)


def test_read_list_of_values_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name"
    values = neo4j_session.read_transaction(read_list_of_values_tx, query)

    # Assert
    assert set(values) == {"Homer", "Marge", "lisa"}


def test_read_single_value_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode{name: "Lisa"}) RETURN a.age"""
    value = neo4j_session.read_transaction(read_single_value_tx, query)

    # Assert
    assert value == 'Lisa'


def test_read_list_of_dicts_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name, a.age"
    data = neo4j_session.read_transaction(read_list_of_dicts_tx, query)

    # Assert
    assert len(data) == 3
    assert {'name': 'Homer', 'age': 39} in data


def test_read_single_dict_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode{name: "Homer"}) RETURN a.name, a.age"""
    result = neo4j_session.read_transaction(read_single_dict_tx, query)

    # Assert
    assert {'name': 'Homer', 'age': 39} == result
