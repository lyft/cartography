from unittest.mock import patch
from tests.integration import settings

from cartography.driftdetect.cli import CLI
from cartography.driftdetect.detect_drift import update_detectors


@patch('cartography.driftdetect.cli.run_update')
def test_cli_main(mock_run):
    cli = CLI(prog="driftdetect")
    cli.main(["--neo4j-uri", settings.get("NEO4J_URL"), "--drift-detection-directory", "tests/data/detectors"])
    mock_run.assert_called_once()


def test_configurate():
    cli = CLI(prog="driftdetect")
    config = cli.configure([
        "--neo4j-uri",
        settings.get("NEO4J_URL"),
        "--drift-detection-directory",
        "tests/data/detectors"
    ])
    assert config.drift_detection_directory == "tests/data/detectors"
    assert config.neo4j_uri == settings.get("NEO4J_URL")


def test_run(neo4j_session):
    """
    Test that a full run through with the CLI works
    :param neo4j_session:
    :return:
    """
    data = [
        ["1", "8", ["15", "22", "29"]],
        ["2", "9", ["16", "23", "30"]],
        ["3", "10", ["17", "24", "31"]],
        ["4", "11", ["18", "25", "32"]],
        ["5", "12", ["19", "26", "33"]],
        ["6", "13", ["20", "27", "34"]],
        ["7", "14", ["21", "28", "35"]],
        ["36", "37", ["38", "39", "40"]]
    ]
    ingest_nodes = """
    MERGE (person:Person{test: {test}})
    SET person.test2 = {test2},
    person.test3 = {test3}
    """
    for node in data:
        test = node[0]
        test2 = node[1]
        test3 = node[2]
        neo4j_session.run(
            ingest_nodes,
            test=test,
            test2=test2,
            test3=test3
        )
    cli = CLI(prog="driftdetect")

    # Test that run does not work with no directory specified

    cli.main([
        "--neo4j-uri",
        settings.get("NEO4J_URL"),
        "--drift-detection-directory",
        "tests/data/test_cli_detectors"
    ])
    update_detectors(neo4j_session, "tests/data/test_cli_detectors", "2.json")

    cli.main([
        "--start-state",
        "tests/data/test_cli_detectors/detector/1.json",
        "--end-state",
        "tests/data/test_cli_detectors/detector/2.json"
    ])
    assert False
