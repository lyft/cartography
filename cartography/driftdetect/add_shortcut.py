import os
import logging
from marshmallow import ValidationError
from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.serializers import ShortcutSchema

logger = logging.getLogger(__name__)


def run_add_shortcut(config):
    """
    Runs add_shortcut from the command line. Does error handling.

    :type config: Config Object
    :param config: Config of adding shortcut
    :return:
    """
    if not os.path.isfile(os.path.join(config.query_directory, config.file)):
        msg = "File does not exist."
        logger.error(msg)
        return
    try:
        add_shortcut(FileSystem, ShortcutSchema(), config.query_directory, config.shortcut, config.file)
    except ValidationError as err:
        msg = "Could not load report_info file from {0}.".format(err.messages)
        logger.exception(msg)


def add_shortcut(storage, shortcut_serializer, query_directory, alias, file):
    """
    Adds a shortcut to the Report_Info File. If a shortcut already exists for an alias, it replaces that shortcut.

    :type storage: Storage Object.
    :param storage: Type of Storage System.
    :type shortcut_serializer: Shortcut Schema.
    :param shortcut_serializer: Shortcut Serializer. Should serialize and deserialize between JSON and Shortcut Object
    :type query_directory: String.
    :param query_directory: Path to Query Directory.
    :type alias: String.
    :param alias: Alias for the file.
    :type file: String.
    :param file: Name of file.
    :return: shortcut object.
    """
    shortcut_path = os.path.join(query_directory, "shortcut.json")
    shortcut_data = storage.load(shortcut_path)
    shortcut = shortcut_serializer.load(shortcut_data)
    shortcut.shortcuts[alias] = file
    new_shortcut_data = shortcut_serializer.dump(shortcut)
    storage.write(new_shortcut_data, shortcut_path)
    return shortcut
