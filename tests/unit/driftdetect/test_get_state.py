
from unittest.mock import MagicMock


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
