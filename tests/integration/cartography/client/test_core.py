from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import read_single_dict_tx
from cartography.client.core.tx import read_single_value_tx
from cartography.client.core.tx import read_list_of_tuples_tx


def _ensure_test_data(neo4j_session):
    neo4j_session.run("""
            MERGE (t1:TestNode{name: "Homer", age: 39})
            MERGE (t2:TestNode{name: "Lisa", age: 8})
            MERGE (t3:TestNode{name: "Marge", age: 36})
        """)


def test_read_list_of_values_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name ORDER BY a.name"
    values = neo4j_session.read_transaction(read_list_of_values_tx, query)

    # Assert
    assert values == ["Homer", "Lisa", "Marge"]


def test_read_single_value_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode{name: "Lisa"}) RETURN a.age"""
    value = neo4j_session.read_transaction(read_single_value_tx, query)

    # Assert
    assert value == 8


def test_read_list_of_dicts_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"
    data = neo4j_session.read_transaction(read_list_of_dicts_tx, query)

    # Assert
    assert len(data) == 3
    assert data[0]['name'] == 'Lisa'
    assert {'name': 'Homer', 'age': 39} in data


def test_read_single_dict_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = """MATCH (a:TestNode{name: "Homer"}) RETURN a.name AS name, a.age AS age"""
    result = neo4j_session.read_transaction(read_single_dict_tx, query)

    # Assert
    assert {'name': 'Homer', 'age': 39} == result


def test_read_list_of_tuples_tx(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    query = "MATCH (a:TestNode) RETURN a.name AS name, a.age AS age ORDER BY age"
    data = neo4j_session.read_transaction(read_list_of_tuples_tx, query)

    # Assert
    assert len(data) == 3
    assert data[0][0] == 'Lisa'
