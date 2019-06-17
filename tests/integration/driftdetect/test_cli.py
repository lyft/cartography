from driftdetect.cli import CLI
from unittest.mock import patch
from tests.integration import settings


@patch('driftdetect.cli.run')
def test_cli_main(mock_run):
    cli = CLI(prog="driftdetect")
    cli.main(["--neo4j-uri", settings.get("NEO4J_URL"), "-d", "tests/data/detectors"])
    mock_run.assert_called_once()


def test_configurate():
    cli = CLI(prog="driftdetect")
    config = cli.configurate(["--neo4j-uri", settings.get("NEO4J_URL"), "-d", "tests/data/detectors"])
    assert config.drift_detector_directory == "tests/data/detectors"
    assert config.neo4j_uri == settings.get("NEO4J_URL")
