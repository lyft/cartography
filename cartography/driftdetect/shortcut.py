import logging

logger = logging.getLogger(__name__)


class Shortcut:
    """
    Interface for ReportInfo Class.

    :type name: String
    :param name: Name of query
    :type shortcuts: Dictionary
    :param shortcuts: Dictionary of Shortcuts to Filenames
    """

    def __init__(self, name, shortcuts):
        self.name = name
        self.shortcuts = shortcuts
