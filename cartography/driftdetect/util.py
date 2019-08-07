import logging
import pathlib

logger = logging.getLogger(__name__)


def valid_directory(directory):
    """
    Error handling for validating directory.

    :type directory: string
    :param directory: Path to directory.
    :return:
    """
    if not directory:
        logger.info("Cannot perform drift-detection because no job path was provided.")
        return False
    drift_detection_directory = pathlib.Path(directory)
    if not drift_detection_directory.exists():
        logger.warning(
            "Cannot perform drift-detection because the provided job path '%s' does not exist.",
            drift_detection_directory,
        )
        return False
    if not drift_detection_directory.is_dir():
        logger.warning(
            "Cannot perform drift-detection because the provided job path '%s' is not a directory.",
            drift_detection_directory,
        )
        return False
    return True
