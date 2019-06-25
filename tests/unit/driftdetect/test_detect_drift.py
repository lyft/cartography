from cartography.driftdetect.update_drift import valid_directory
from cartography.driftdetect.config import Config
from cartography.driftdetect.detect_drift import perform_drift_detection


def test_valid_directory():
    config = Config("tests", "localhost")
    assert valid_directory(config)
    config.drift_detection_directory = "temp"
    assert not valid_directory(config)


def test_perform_drift_detection():
    start_state = "tests/data/test_cli_detectors/detector/1.json"
    end_state = "tests/data/test_cli_detectors/detector/2.json"
    new_results, missing_results = perform_drift_detection(start_state, end_state)
    new_results = [drift_info_detector_pair[0] for drift_info_detector_pair in new_results]
    missing_results = [drift_info_detector_pair[0] for drift_info_detector_pair in missing_results]
    assert {'d.test': '36', 'd.test2': '37', 'd.test3': ['38', '39', '40']} in new_results
    assert {'d.test': '7', 'd.test2': '14', 'd.test3': ['21', '28', '35']} in missing_results
