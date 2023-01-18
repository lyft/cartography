import cartography.intel.hibob.employees
import tests.data.hibob.employees


TEST_UPDATE_TAG = 123456789


def test_load_hibob_employees(neo4j_session):

    data = tests.data.hibob.employees.HIBOB_EMPLOYEES_GET_DATA
    departments, employees = cartography.intel.hibob.employees.transform(data)
    cartography.intel.hibob.employees.load(
        neo4j_session,
        departments,
        employees,
        TEST_UPDATE_TAG,
    )

    # Ensure employees got loaded
    nodes = neo4j_session.run(
        """
        MATCH (e:HiBobEmployee) RETURN e.id, e.email;
        """,
    )
    expected_nodes = {
        ("1234", 'john.doe@domain.tld'),
        ("5678", 'jane.smith@domain.tld'),
    }
    actual_nodes = {
        (
            n['e.id'],
            n['e.email'],
        ) for n in nodes
    }
    assert actual_nodes == expected_nodes

    # Check manager links
    nodes = neo4j_session.run(
        """
        MATCH(e:HiBobEmployee)-[:MANAGED_BY]->(m:HiBobEmployee)
        RETURN e.id, m.id
        """,
    )
    actual_nodes = {
        (
            n['e.id'],
            n['m.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            '1234',
            '5678',
        ),
    }
    assert actual_nodes == expected_nodes

    # Check org links
    nodes = neo4j_session.run(
        """
        MATCH(e:HiBobEmployee)-[:MEMBER_OF]->(d:HiBobDepartment)
        RETURN e.id, d.id
        """,
    )
    actual_nodes = {
        (
            n['e.id'],
            n['d.id'],
        ) for n in nodes
    }
    expected_nodes = {
        (
            '1234',
            'R&D',
        ),
        (
            '5678',
            'R&D',
        ),
    }
    assert actual_nodes == expected_nodes
