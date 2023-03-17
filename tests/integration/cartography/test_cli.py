from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.cli
from cartography.cli import CLI
from tests.integration import settings


def test_cli():
    """
    Simulate running `cartography --neo4j-uri URI sync` and ensure the sync gets run.
    """
    sync = MagicMock()
    cli = CLI(sync, 'test')
    cli.main(["--neo4j-uri", settings.get("NEO4J_URL"), "sync"])
    sync.run.assert_called_once()


@patch.object(cartography.cli, 'run_with_config', return_value=0)
def test_cli_load_yaml(mock_run_with_config: MagicMock):
    """
    Simulate running `cartography --config tests/data/test_cartography_conf.yaml` and ensure that the sync starts.
    """
    argv = [
        "--config",
        "tests/data/test_cartography_conf.yaml",
        "sync",
    ]

    # Act
    CLI(prog='cartography').main(argv)

    # Assert
    mock_run_with_config.assert_called()


# TODO test that the okta_saml_role_regex reaches the AWS module as expected
