import os
import os.path
import logging
from driftdetect.driftdetector import load_detector_from_json_file, write_detector_to_json_file
from marshmallow import ValidationError


logger = logging.getLogger(__name__)


def perform_drift_detection(session, expect_folder, update):
    """
    Perform Drift Detection
    :param session: neo4j_session
    :param expect_folder: detector directory
    :param update: boolean
    :return:
    """
    drift_info_detector_pairs = []
    for root, _, filenames in os.walk(expect_folder):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            try:
                detector = load_detector_from_json_file(file_path)
                for drift_info in detector.run(session, update):
                    drift_info_detector_pairs.append((drift_info, detector))
                if update:
                    try:
                        write_detector_to_json_file(detector, file_path)
                    except ValidationError as err:
                        msg = "Unable to save DriftDetector from file {0} for \n{1}".format(file_path, err.messages)
                        logger.error(msg, exc_info=True)
            except ValidationError as err:
                msg = "Unable to create DriftDetector from file {0} for \n{1}".format(file_path, err.messages)
                logger.error(msg, exc_info=True)
    return drift_info_detector_pairs
