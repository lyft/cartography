from cartography.driftdetect.cli import valid_directory
from cartography.driftdetect.config import Config


def test_valid_directory():
    config = Config("tests", "localhost")
    assert valid_directory(config)
    config.drift_detection_directory = "temp"
    assert not valid_directory(config)
