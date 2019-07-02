from unittest.mock import patch

from tests.integration import settings
from cartography.driftdetect.cli import CLI
from cartography.driftdetect.report_info import load_report_info_from_json_file, write_report_info_to_json_file


@patch('cartography.driftdetect.cli.run_update')
def test_cli_main(mock_run):
    cli = CLI(prog="cartography-detectdrift")
    cli.main(["update",
              "--neo4j-uri",
              settings.get("NEO4J_URL"),
              "--drift-detection-directory",
              "tests/data/test_update_detectors"])
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
    start_state = "1.json"
    end_state = "2.json"
    directory = "tests/data/test_cli_detectors/detector"
    cli = CLI(prog="cartography-detectdrift")
    cli.main(["get-drift",
              "--query-directory",
              directory,
              "--start-state",
              start_state,
              "--end-state",
              end_state])
    assert mock_report_drift.call_count == 2


@patch('cartography.driftdetect.cli.report_drift')
def test_cli_shortcuts(mock_report_drift):
    start_state = "1.json"
    end_state = "most_recent_file"
    directory = "tests/data/test_cli_detectors/detector"
    cli = CLI(prog="cartography-detectdrift")
    cli.main(["get-drift",
              "--query-directory",
              directory,
              "--start-state",
              start_state,
              "--end-state",
              end_state])


def test_add_shortcuts():
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    shortcut = "test_shortcut"
    file = "1.json"
    report_info_path = directory + '/report_info.json'
    cli.main(["add-shortcut",
              "--query-directory",
              directory,
              "--shortcut",
              shortcut,
              "--file",
              file])
    report_info = load_report_info_from_json_file(report_info_path)
    assert report_info.shortcuts[shortcut] == file
    report_info.shortcuts.pop(shortcut)
    write_report_info_to_json_file(report_info, report_info_path)
