from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.sync
from cartography.cli import CLI


def test_cli_selected_modules():
    """
    Test that we correctly parse the --selected-modules arg
    """
    # Arrange
    argv = [
        "sync",
        "--selected-modules",
        "aws",
    ]

    # Act
    cli = CLI(prog='cartography')

    # Assert that the argparser created by the CLI knows that we want to run the aws module
    parsed_args = cli.parser.parse_args(argv)
    assert parsed_args.selected_modules == 'aws'


@patch.object(cartography.cli, 'run_with_config', return_value=0)
def test_cli_main(mock_run_with_config: MagicMock):
    """
    Test that processing a cartography Config object with CLI.main() works.
    """
    argv = [
        "sync",
        "--selected-modules",
        "aws",
    ]

    # Act
    CLI(prog='cartography').main(argv)

    # Assert
    mock_run_with_config.assert_called()
