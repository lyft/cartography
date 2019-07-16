from cartography.driftdetect.detect_deviations import stitch_drift_detection


def test_perform_drift_detection():
    """
    Tests that drift detection works.
    """
    start_state = "1.json"
    end_state = "2.json"
    directory = "tests/data/test_cli_detectors/detector"
    new_results, missing_results = stitch_drift_detection(directory, start_state, end_state)
    new_results = [drift_info_detector_pair[0] for drift_info_detector_pair in new_results]
    missing_results = [drift_info_detector_pair[0] for drift_info_detector_pair in missing_results]
    assert {'d.test': '36', 'd.test2': '37', 'd.test3': ['38', '39', '40']} in new_results
    assert {'d.test': '7', 'd.test2': '14', 'd.test3': ['21', '28', '35']} in missing_results
