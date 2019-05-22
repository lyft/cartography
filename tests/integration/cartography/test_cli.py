import cartography.cli
import unittest.mock


def test_cli():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, 'test')
    cli.main("")
    sync.run.assert_called_once()
