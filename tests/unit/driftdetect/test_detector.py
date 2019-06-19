from driftdetect.driftdetector import load_detector_from_json_file
from driftdetect.detect_drift import get_drift_from_detectors
from unittest.mock import MagicMock


def test_detector_no_drift():
    """
    Test that a detector that detects no drift returns none.
    :return:
    """
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    key = "key"
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
    key = "baseline_tag"
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
    key_1 = "baseline_tag"
    key_2 = "other_tag"
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
    Tests fields with multiple properties handles correctly.
    :return:
    """
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    key_1 = "key_1"
    key_2 = "key_2"
    key_3 = "key_3"
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
    Tests full run through of drift detection.
    :return:
    """
    key = "baseline_tag"
    key_1 = "baseline_tag"
    key_2 = "other_tag"
    mock_session = MagicMock()
    mock_boltstatementresult_1 = MagicMock()
    mock_boltstatementresult_2 = MagicMock()
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

    mock_boltstatementresult_1.__getitem__.side_effect = results_1.__getitem__
    mock_boltstatementresult_1.__iter__.side_effect = results_1.__iter__
    mock_boltstatementresult_2.__getitem__.side_effect = results_2.__getitem__
    mock_boltstatementresult_2.__iter__.side_effect = results_2.__iter__

    def mock_session_side_effect(*args, **kwargs):
        if args[0] == "MATCH (d) RETURN d.test":
            return mock_boltstatementresult_1
        else:
            return mock_boltstatementresult_2

    mock_session.run.side_effect = mock_session_side_effect
    detectors = []
    detectors.append(load_detector_from_json_file("tests/data/detectors/test_expectations.json"))
    detectors.append(load_detector_from_json_file("tests/data/detectors/test_multiple_expectations.json"))
    drifts = []
    for drift_info, detector in get_drift_from_detectors(mock_session, detectors, False):
        drifts.append(drift_info)

    assert {key_1: "7", key_2: "14"} in drifts
    assert {key: "7"} in drifts
    assert {key_1: "3", key_2: "10"} not in drifts


def test_json_loader():
    """
    Tests loading schema passes
    :return:
    """
    filepath = "tests/data/detectors/test_expectations.json"
    detector = load_detector_from_json_file(filepath)
    assert detector.name == "Test-Expectations"
    assert detector.validation_query == "MATCH (d) RETURN d.test"
    assert str(detector.detector_type) == "DriftDetectorType.EXPOSURE"
    assert detector.expectations == [['1'], ['2'], ['3'], ['4'], ['5'], ['6']]
