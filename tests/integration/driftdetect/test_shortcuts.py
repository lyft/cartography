import os

from cartography.driftdetect.storage import FileSystem
from cartography.driftdetect.serializers import ShortcutSchema
from cartography.driftdetect.cli import CLI


def test_basic_add_shortcuts():
    """
    Tests that the CLI can add shortcuts.
    """
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "test_shortcut"
    file = "1.json"
    shortcut_path = directory + '/shortcut.json'
    cli.main(["add-shortcut",
              "--query-directory",
              directory,
              "--shortcut",
              alias,
              "--file",
              file])
    shortcut_data = FileSystem.load(shortcut_path)
    shortcut = ShortcutSchema().load(shortcut_data)
    assert shortcut.shortcuts[alias] == file
    shortcut.shortcuts.pop(alias)
    shortcut_data = ShortcutSchema().dump(shortcut)
    FileSystem.write(shortcut_data, shortcut_path)


def test_nonexistent_shortcuts():
    cli = CLI(prog="cartography-detectdrift")
    directory = "tests/data/test_cli_detectors/detector"
    alias = "test_shortcut"
    file = "3.json"
    shortcut_path = os.path.join(directory, "shortcut.json")
    cli.main(["add-shortcut",
              "--query-directory",
              directory,
              "--shortcut",
              alias,
              "--file",
              file])
    shortcut_data = FileSystem.load(shortcut_path)
    shortcut = ShortcutSchema().load(shortcut_data)
    try:
        shortcut.shortcuts[alias]
    except KeyError:
        pass
