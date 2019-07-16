import os
import logging
from marshmallow import ValidationError
from cartography.driftdetect.report_info import load_report_info_from_json_file, write_report_info_to_json_file

logger = logging.getLogger(__name__)


def run_add_shortcut(config):
    try:
        add_shortcut(config.query_directory, config.shortcut, config.file)
    except ValidationError as err:
        msg = "Could not load report_info file."
        logger.exception(msg, err.messages)


def add_shortcut(directory, alias, file):
    """
    Adds a shortcut to the Report_Info File. If a shortcut already exists for an alias, it replaces that shortcut.

    :type directory: String
    :param directory: A path to a directory containing drift-states for a specific query.
    :type alias: String
    :param alias: The desired name to replace the filename.
    :type file: String
    :param file: The desired name of the file to be replace (no directory prefix).
    :return:
    """
    report_info_path = os.path.join(directory, "report_info.json")
    misc = load_report_info_from_json_file(report_info_path)
    misc.shortcuts[alias] = file
    write_report_info_to_json_file(misc, report_info_path)
