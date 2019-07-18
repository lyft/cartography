from unittest.mock import MagicMock

from cartography.driftdetect.model import State
from cartography.driftdetect.serializers import StateSchema
from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.get_states import get_state
from cartography.driftdetect.detect_deviations import compare_states, perform_drift_detection


def test_state_no_drift():
    """
    Test that a state that detects no drift returns none.
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
    data = FileSystem.load("tests/data/detectors/test_expectations.json")
    state_old = StateSchema().load(data)
    state_new = State(state_old.name, state_old.validation_query, state_old.properties, [])
    get_state(mock_session, state_new)
    drifts = compare_states(state_old, state_new)
    mock_session.run.assert_called_with(state_new.validation_query)
    assert not drifts


def test_state_picks_up_drift():
    """
    Test that a state that detects drift.
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
    data = FileSystem.load("tests/data/detectors/test_expectations.json")
    state_old = StateSchema().load(data)
    state_new = State(state_old.name, state_old.validation_query, state_old.properties, [])
    get_state(mock_session, state_new)
    drifts = compare_states(state_old, state_new)
    mock_session.run.assert_called_with(state_new.validation_query)
    assert drifts
    assert drifts[0][0] == {key: "7"}


def test_state_multiple_expectations():
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
    data = FileSystem.load("tests/data/detectors/test_multiple_expectations.json")
    state_old = StateSchema().load(data)
    state_new = State(state_old.name, state_old.validation_query, state_old.properties, [])
    get_state(mock_session, state_new)
    drifts = compare_states(state_old, state_new)
    mock_session.run.assert_called_with(state_new.validation_query)
    assert {key_1: "7", key_2: "14"} in drifts[0]


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
    data = FileSystem.load("tests/data/detectors/test_multiple_properties.json")
    state_old = StateSchema().load(data)
    state_new = State(state_old.name, state_old.validation_query, state_old.properties, [])
    get_state(mock_session, state_new)
    drifts = compare_states(state_old, state_new)
    mock_session.run.assert_called_with(state_new.validation_query)
    print(drifts)
    assert {key_1: "7", key_2: "14", key_3: ["21", "28", "35"]} in drifts[0]
    assert {key_1: "3", key_2: "10", key_3: ["17", "24", "31"]} not in drifts[0]


def test_json_loader():
    """
    Test loading schema passes
    :return:
    """

    filepath = "tests/data/detectors/test_expectations.json"
    data = FileSystem.load(filepath)
    state = StateSchema().load(data)
    assert state.name == "Test-Expectations"
    assert state.validation_query == "MATCH (d) RETURN d.test"
    assert state.results == [['1'], ['2'], ['3'], ['4'], ['5'], ['6']]


def test_state_differences():
    """
    Test that state_differences picks up new drift
    :return:
    """

    filepath = "tests/data/detectors/test_expectations.json"
    data = FileSystem.load(filepath)
    state_1 = StateSchema().load(data)
    state_2 = StateSchema().load(data)
    state_2.results.append(["7"])
    drift_info_state_pairs = compare_states(state_1, state_2)
    assert ({'d.test': "7"}, state_2) in drift_info_state_pairs


def test_compare_states():
    """
    Test that differences between two states is recorded
    :return:
    """

    filepath = "tests/data/detectors/test_expectations.json"
    data = FileSystem.load(filepath)
    state_1 = StateSchema().load(data)
    state_2 = StateSchema().load(data)
    state_1.results.append(["7"])
    state_2.results.append(["8"])
    new, missing = perform_drift_detection(state_1, state_2)
    assert ({'d.test': "7"}, state_1) in missing
    assert ({'d.test': "8"}, state_2) in new
