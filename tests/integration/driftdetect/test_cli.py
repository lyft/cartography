from unittest.mock import patch

from tests.integration import settings
from cartography.driftdetect.cli import CLI


@patch('cartography.driftdetect.cli.run_update')
def test_cli_main(mock_run):
    cli = CLI(prog="cartography-detectdrift")
    cli.main(["update",
              "--neo4j-uri",
              settings.get("NEO4J_URL"),
              "--drift-detection-directory",
              "tests/data/detectors"])
    mock_run.assert_called_once()


def test_configurate():
    cli = CLI(prog="cartography-detectdrift")
    config = cli.configure([
        "update",
        "--neo4j-uri",
        settings.get("NEO4J_URL"),
        "--drift-detection-directory",
        "tests/data/detectors"
    ])
    assert config.drift_detection_directory == "tests/data/detectors"
    assert config.neo4j_uri == settings.get("NEO4J_URL")


@patch('cartography.driftdetect.cli.report_drift')
def test_cli_get_drift(mock_report_drift):
    start_state = "tests/data/test_cli_detectors/detector/1.json"
    end_state = "tests/data/test_cli_detectors/detector/2.json"
    directory = "tests/data/test_cli_detectors/detector"
    cli = CLI(prog="carogtaphy-detectdrift")
    cli.main(["get-drift",
              "--drift-detection-directory",
              directory,
              "--start-state",
              start_state,
              "--end-state",
              end_state])
    assert mock_report_drift.call_count == 2
