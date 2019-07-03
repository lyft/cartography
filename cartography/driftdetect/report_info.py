import os
import json
import logging
from marshmallow import Schema, fields, post_load

logger = logging.getLogger(__name__)


class ReportInfo:
    """
    Interface for ReportInfo Class.

    :type name: String
    :param name: Name of query
    :type shortcuts: Dictionary
    :param shortcuts: Dictionary of Shortcuts to Filenames
    :type detector_type: DriftDetectorType
    :param detector_type: DriftDetectorType
    """
    def __init__(self, name, shortcuts):
        self.name = name
        self.shortcuts = shortcuts


class ReportInfoSchema(Schema):
    """
    Schema for ReportInfo Object.
    """
    name = fields.Str()
    shortcuts = fields.Dict(keys=fields.Str(), values=fields.Str())
    detector_type = fields.Int()

    @post_load
    def make_misc(self, data, **kwargs):
        return ReportInfo(
            data['name'],
            data['shortcuts'])


def load_report_info_from_json_file(file_path):
    """
    Creates misc object from Json File.

    :type file_path: string
    :param file_path: path to json file that detector is created from
    :return: DriftDetector
    """
    logger.debug("Creating from json file {0}".format(file_path))
    with open(file_path) as j_file:
        data = json.load(j_file)
    schema = ReportInfoSchema()
    misc = schema.load(data)
    return misc


def write_report_info_to_json_file(misc, file_path):
    """
    Saves misc object to json file.

    :type misc: DriftDetector
    :param misc: Detector to be saved
    :type file_path: string
    :param file_path: file_path to store detector
    :return: None
    """
    logger.debug("Saving to json file {0}".format(file_path))
    schema = ReportInfoSchema()
    data = schema.dump(misc)
    with open(file_path, 'w') as j_file:
        json.dump(data, j_file, indent=4)


def add_shortcut(directory, shortcut, file):
    """
    Adds a shortcut to the Report_Info File.

    :type directory: String
    :param directory: A path to a directory containing drift-states for a specific query.
    :type shortcut: String
    :param shortcut: The desired name to replace the filename.
    :type file: String
    :param file: The desired name of the file to be replace (no directory prefix).
    :return:
    """
    report_info_path = os.path.join(directory, "report_info.json")
    misc = load_report_info_from_json_file(report_info_path)
    misc.shortcuts[shortcut] = file
    write_report_info_to_json_file(misc, report_info_path)
