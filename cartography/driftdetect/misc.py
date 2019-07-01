import json
import logging
from marshmallow import Schema, fields, post_load
from enum import IntEnum

logger = logging.getLogger(__name__)


class DriftDetectorType(IntEnum):
    EXPOSURE = 1


class Misc:
    def __init__(self, name, shortcuts, detector_type):
        self.name = name
        self.shortcuts = shortcuts
        self.detector_type = detector_type


class MiscSchema(Schema):
    name = fields.Str()
    shortcuts = fields.Dict(keys=fields.Str(), values=fields.Str())
    detector_type = fields.Int()

    @post_load
    def make_misc(self, data, **kwargs):
        return Misc(data['name'],
                    data['shortcuts'],
                    DriftDetectorType(data['detector_type']))


def load_misc_from_json_file(file_path):
    """
    Creates misc object from Json File
    :type file_path: string
    :param file_path: path to json file that detector is created from
    :return: DriftDetector
    """
    logger.debug("Creating from json file {0}".format(file_path))
    with open(file_path) as j_file:
        data = json.load(j_file)
    schema = MiscSchema()
    misc = schema.load(data)
    return misc


def write_misc_to_json_file(misc, file_path):
    """
    Saves misc object to json file
    :type misc: DriftDetector
    :param misc: Detector to be saved
    :type file_path: string
    :param file_path: file_path to store detector
    :return: None
    """
    logger.debug("Saving to json file {0}".format(file_path))
    schema = MiscSchema()
    data = schema.dump(misc)
    with open(file_path, 'w') as j_file:
        json.dump(data, j_file, indent=4)
