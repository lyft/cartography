from driftdetect.driftdetector import DriftDetector
from driftdetect.detect_drift import perform_baseline_drift_detection
from unittest.mock import MagicMock


def test_detector_no_drift():
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
    detector = DriftDetector.from_json_file("tests/data/detectors/test_expectations.json")
    drifts = []
    for it in detector.run(mock_session):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    assert not drifts


def test_detector_picks_up_drift():
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
    detector = DriftDetector.from_json_file("tests/data/detectors/test_expectations.json")
    drifts = []
    for it in detector.run(mock_session):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    assert drifts
    assert drifts[0] == {key: "7"}


def test_perform_baseline_drift_detection():
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
    pairs = []
    for drift_info, detector in perform_baseline_drift_detection(mock_session, expect_folder="tests/data/detectors"):
        pairs.append((drift_info, detector))
    assert pairs[0][0][key] == "7"


def test_json_loader():
    filepath = "tests/data/detectors/test_expectations.json"
    detector = DriftDetector.from_json_file(filepath)
    assert detector.name == "Test-Expectations"
    assert detector.validation_query == "MATCH (d) RETURN d.baseline"
    assert str(detector.detector_type) == "DriftDetectorType.EXPOSURE"
    assert detector.expectations == [['1'], ['2'], ['3'], ['4'], ['5'], ['6']]
