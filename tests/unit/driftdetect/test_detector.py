from unittest.mock import MagicMock

from cartography.driftdetect.driftdetector import load_detector_from_json_file
from cartography.driftdetect.detect_drift import perform_drift_detection, detector_differences, compare_detectors


def test_detector_no_drift():
    """
    Test that a detector that detects no drift returns none.
    :return:
    """
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    key = "d.test"
    results = [
        {key: "1"},
        {key: "2"},
        {key: "3"},
        {key: "4"},
        {key: "5"},
        {key: "6"},
    ]

    mock_boltstatementresult.__getitem__.side_effect = results.__getitem__
    mock_boltstatementresult.__iter__.side_effect = results.__iter__
    mock_session.run.return_value = mock_boltstatementresult
    detector = load_detector_from_json_file("tests/data/detectors/test_expectations.json")
    drifts = []
    for it in detector.run(mock_session, False):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    assert not drifts


def test_detector_picks_up_drift():
    """
    Test that a detector that detects drift.
    :return:
    """
    key = "d.test"
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    results = [
        {key: "1"},
        {key: "2"},
        {key: "3"},
        {key: "4"},
        {key: "5"},
        {key: "6"},
        {key: "7"}
    ]

    mock_boltstatementresult.__getitem__.side_effect = results.__getitem__
    mock_boltstatementresult.__iter__.side_effect = results.__iter__
    mock_session.run.return_value = mock_boltstatementresult
    detector = load_detector_from_json_file("tests/data/detectors/test_expectations.json")
    drifts = []
    for it in detector.run(mock_session, False):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    assert drifts
    assert drifts[0] == {key: "7"}


def test_detector_multiple_expectations():
    """
    Test that multiple fields runs properly.
    :return:
    """
    key_1 = "d.test"
    key_2 = "d.test2"
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    results = [
        {key_1: "1", key_2: "8"},
        {key_1: "2", key_2: "9"},
        {key_1: "3", key_2: "10"},
        {key_1: "4", key_2: "11"},
        {key_1: "5", key_2: "12"},
        {key_1: "6", key_2: "13"},
        {key_1: "7", key_2: "14"}
    ]

    mock_boltstatementresult.__getitem__.side_effect = results.__getitem__
    mock_boltstatementresult.__iter__.side_effect = results.__iter__
    mock_session.run.return_value = mock_boltstatementresult
    detector = load_detector_from_json_file("tests/data/detectors/test_multiple_expectations.json")
    drifts = []
    for it in detector.run(mock_session, False):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    assert {key_1: "7", key_2: "14"} in drifts


def test_drift_from_multiple_properties():
    """
    Test fields with multiple properties handles correctly.
    :return:
    """
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    key_1 = "d.test"
    key_2 = "d.test2"
    key_3 = "d.test3"
    results = [
        {key_1: "1", key_2: "8", key_3: ["15", "22", "29"]},
        {key_1: "2", key_2: "9", key_3: ["16", "23", "30"]},
        {key_1: "3", key_2: "10", key_3: ["17", "24", "31"]},
        {key_1: "4", key_2: "11", key_3: ["18", "25", "32"]},
        {key_1: "5", key_2: "12", key_3: ["19", "26", "33"]},
        {key_1: "6", key_2: "13", key_3: ["20", "27", "34"]},
        {key_1: "7", key_2: "14", key_3: ["21", "28", "35"]}
    ]
    mock_boltstatementresult.__getitem__.side_effect = results.__getitem__
    mock_boltstatementresult.__iter__.side_effect = results.__iter__
    mock_session.run.return_value = mock_boltstatementresult
    detector = load_detector_from_json_file("tests/data/detectors/test_multiple_properties.json")
    drifts = []
    for it in detector.run(mock_session, False):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    print(drifts)
    assert {key_1: "7", key_2: "14", key_3: ["21", "28", "35"]} in drifts
    assert {key_1: "3", key_2: "10", key_3: ["17", "24", "31"]} not in drifts


def test_get_drift_from_detectors():
    """
    Test full run through of drift detection.
    :return:
    """

    key = "d.test"
    key_1 = "d.test2"
    key_2 = "d.test3"
    results_1 = [
        {key: "1"},
        {key: "2"},
        {key: "3"},
        {key: "4"},
        {key: "5"},
        {key: "6"},
        {key: "7"}
    ]
    results_2 = [
        {key_1: "1", key_2: "8"},
        {key_1: "2", key_2: "9"},
        {key_1: "3", key_2: "10"},
        {key_1: "4", key_2: "11"},
        {key_1: "5", key_2: "12"},
        {key_1: "6", key_2: "13"},
        {key_1: "7", key_2: "14"}
    ]
    results_3 = [
        {key: "1", key_1: "8", key_2: "15|22|29"},
        {key: "2", key_1: "9", key_2: "16|23|30"},
        {key: "3", key_1: "10", key_2: "17|24|31"},
        {key: "4", key_1: "11", key_2: "18|25|32"},
        {key: "5", key_1: "12", key_2: "19|26|33"},
        {key: "6", key_1: "13", key_2: "20|27|34"}
    ]

    mock_session = MagicMock()
    mock_boltstatementresult_1 = MagicMock()
    mock_boltstatementresult_2 = MagicMock()
    mock_boltstatementresult_3 = MagicMock()
    mock_boltstatementresult_1.__getitem__.side_effect = results_1.__getitem__
    mock_boltstatementresult_1.__iter__.side_effect = results_1.__iter__
    mock_boltstatementresult_2.__getitem__.side_effect = results_2.__getitem__
    mock_boltstatementresult_2.__iter__.side_effect = results_2.__iter__
    mock_boltstatementresult_3.__getitem__.side_effect = results_3.__getitem__
    mock_boltstatementresult_3.__iter__.side_effect = results_3.__iter__

    def mock_session_side_effect(*args, **kwargs):
        if args[0] == "MATCH (d) RETURN d.test":
            return mock_boltstatementresult_1
        elif args[0] == "MATCH (d) RETURN d.test,d.test2":
            return mock_boltstatementresult_2
        else:
            return mock_boltstatementresult_3

    mock_session.run.side_effect = mock_session_side_effect

    drifts = []
    for drift_info, detector in perform_drift_detection(mock_session, "tests/data/detectors", False):
        drifts.append(drift_info)

    assert {key_1: "7", key_2: "14"} in drifts
    assert {key: "7"} in drifts
    assert {key_1: "3", key_2: "10"} not in drifts


def test_json_loader():
    """
    Test loading schema passes
    :return:
    """

    filepath = "tests/data/detectors/test_expectations.json"
    detector = load_detector_from_json_file(filepath)
    assert detector.name == "Test-Expectations"
    assert detector.validation_query == "MATCH (d) RETURN d.test"
    assert str(detector.detector_type) == "DriftDetectorType.EXPOSURE"
    assert detector.expectations == [['1'], ['2'], ['3'], ['4'], ['5'], ['6']]


def test_detector_differences():
    """
    Test that detector_differences picks up new drift
    :return:
    """

    filepath = "tests/data/detectors/test_expectations.json"
    detector_1 = load_detector_from_json_file(filepath)
    detector_2 = load_detector_from_json_file(filepath)
    detector_2.expectations.append(["7"])
    drift_info_detector_pairs = detector_differences(detector_1, detector_2)
    assert ({'d.test': "7"}, detector_2) in drift_info_detector_pairs


def test_compare_detectors():
    """
    Test that differences between two detectors is recorded
    :return:
    """

    filepath = "tests/data/detectors/test_expectations.json"
    detector_1 = load_detector_from_json_file(filepath)
    detector_2 = load_detector_from_json_file(filepath)
    detector_1.expectations.append(["7"])
    detector_2.expectations.append(["8"])
    new, missing = compare_detectors(detector_1, detector_2)
    assert ({'d.test': "7"}, detector_1) in missing
    assert ({'d.test': "8"}, detector_2) in new
