from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.serializers import StateSchema
from cartography.driftdetect.detect_deviations import perform_drift_detection


def test_perform_drift_detection():
    """
    Tests that drift detection works.
    """
    data = FileSystem.load("tests/data/test_cli_detectors/detector/1.json")
    start_state = StateSchema().load(data)
    data = FileSystem.load("tests/data/test_cli_detectors/detector/2.json")
    end_state = StateSchema().load(data)
    new_results, missing_results = perform_drift_detection(start_state, end_state)
    new_results = [drift_info_detector_pair[0] for drift_info_detector_pair in new_results]
    missing_results = [drift_info_detector_pair[0] for drift_info_detector_pair in missing_results]
    assert {'d.test': '36', 'd.test2': '37', 'd.test3': ['38', '39', '40']} in new_results
    assert {'d.test': '7', 'd.test2': '14', 'd.test3': ['21', '28', '35']} in missing_results
