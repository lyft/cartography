import cartography.cli
import unittest.mock


def test_cli():
    sync = unittest.mock.MagicMock()
    cli = cartography.cli.CLI(sync, 'test')
    cli.main(["--neo4j-uri", "bolt://infraintelgraph-legacy.devbox.lyft.net:7687"])
    sync.run.assert_called_once()
