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


def load_report_info_from_json(file_content):
    """
    Creates ReportInfo from JSON File
    :type file_content: JSON
    :param file_content: ReportInfo Information in JSON format
    :return: ReportInfo
    """
    data = json.load(file_content)
    schema = ReportInfoSchema()
    report_info = schema.load(data)
    return report_info


def write_report_info_to_json(report_info):
    """
    Saves detector to JSON file
    :type report_info: ReportInfo
    :param report_info: ReportInfo to be saved
    :return: None
    """
    schema = ReportInfoSchema()
    data = schema.dump(report_info)
    return data


def load_report_info_from_json_file(file_path):
    """
    Creates misc object from JSON File.

    :type file_path: string
    :param file_path: path to JSON file that ReportInfo is created from
    :return: ReportInfo
    """
    logger.debug("Creating from json file {0}".format(file_path))
    with open(file_path) as j_file:
        report_info = load_report_info_from_json(j_file)
    return report_info


def write_report_info_to_json_file(report_info, file_path):
    """
    Saves misc object to JSON file.

    :type report_info: ReportInfo
    :param report_info: ReportInfo to be saved
    :type file_path: string
    :param file_path: file_path to store ReportInfo
    :return: None
    """
    logger.debug("Saving to JSON file {0}".format(file_path))
    with open(file_path, 'w') as j_file:
        data = write_report_info_to_json(report_info)
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
