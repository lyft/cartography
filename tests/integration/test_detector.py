from driftdetect.driftdetector import DriftDetector
from driftdetect.detect_drift import perform_baseline_drift_detection
from unittest.mock import MagicMock


def test_detector_no_drift():
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    results = [
        {"baseline_tag": "1"},
        {"baseline_tag": "2"},
        {"baseline_tag": "3"},
        {"baseline_tag": "4"},
        {"baseline_tag": "5"},
        {"baseline_tag": "6"},
    ]

    mock_boltstatementresult.__getitem__.side_effect = results.__getitem__
    mock_boltstatementresult.__iter__.side_effect = results.__iter__
    mock_session.run.return_value = mock_boltstatementresult
    detector = DriftDetector.from_json_file("tests/data/detectors/test_expectations.json").data
    drifts = []
    for it in detector.run(mock_session):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    assert not drifts


def test_detector_picks_up_drift():
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    results = [
        {"baseline_tag": "1"},
        {"baseline_tag": "2"},
        {"baseline_tag": "3"},
        {"baseline_tag": "4"},
        {"baseline_tag": "5"},
        {"baseline_tag": "6"},
        {"baseline_tag": "7"}
    ]

    mock_boltstatementresult.__getitem__.side_effect = results.__getitem__
    mock_boltstatementresult.__iter__.side_effect = results.__iter__
    mock_session.run.return_value = mock_boltstatementresult
    detector = DriftDetector.from_json_file("tests/data/detectors/test_expectations.json").data
    drifts = []
    for it in detector.run(mock_session):
        drifts.append(it)
    mock_session.run.assert_called_with(detector.validation_query)
    assert drifts
    assert drifts[0] == {"baseline_tag": "7"}


def test_perform_baseline_drift_detection():
    mock_session = MagicMock()
    mock_boltstatementresult = MagicMock()
    results = [
        {"baseline_tag": "1"},
        {"baseline_tag": "2"},
        {"baseline_tag": "3"},
        {"baseline_tag": "4"},
        {"baseline_tag": "5"},
        {"baseline_tag": "6"},
        {"baseline_tag": "7"}
    ]

    mock_boltstatementresult.__getitem__.side_effect = results.__getitem__
    mock_boltstatementresult.__iter__.side_effect = results.__iter__
    mock_session.run.return_value = mock_boltstatementresult
    pairs = []
    for drift_info, detector in perform_baseline_drift_detection(mock_session, expect_folder="tests/data/detectors"):
        pairs.append((drift_info, detector))
    assert pairs[0][0]["baseline_tag"] == "7"


def test_json_loader():
    filepath = "tests/data/detectors/test_expectations.json"
    detector = DriftDetector.from_json_file(filepath).data
    assert detector.name == "Test-Expectations"
    assert detector.validation_query == "MATCH (d) RETURN d.baseline"
    assert str(detector.detector_type) == "DriftDetectorType.EXPOSURE"
    assert detector.expectations == ['1', '2', '3', '4', '5', '6']
