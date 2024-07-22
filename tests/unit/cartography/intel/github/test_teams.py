from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.github.teams import _get_team_repos_for_multiple_teams
from cartography.intel.github.teams import RepoPermission


@patch('cartography.intel.github.teams._get_team_repos')
def test_get_team_repos_empty_team_list(mock_get_team_repos):
    # Assert that if we pass in empty data then we get back empty data
    assert _get_team_repos_for_multiple_teams(
        [],
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {}
    mock_get_team_repos.assert_not_called()


@patch('cartography.intel.github.teams._get_team_repos')
def test_get_team_repos_team_with_no_repos(mock_get_team_repos):
    # Arrange
    team_data = [{'slug': 'team1', 'repositories': {'totalCount': 0}}]

    # Assert that we retrieve data where a team has no repos
    assert _get_team_repos_for_multiple_teams(
        team_data,
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {'team1': []}
    mock_get_team_repos.assert_not_called()


@patch('cartography.intel.github.teams._get_team_repos')
def test_get_team_repos_happy_path(mock_get_team_repos):
    # Arrange
    team_data = [{'slug': 'team1', 'repositories': {'totalCount': 2}}]
    mock_team_repos = MagicMock()
    mock_team_repos.nodes = [{'url': 'https://github.com/org/repo1'}, {'url': 'https://github.com/org/repo2'}]
    mock_team_repos.edges = [{'permission': 'WRITE'}, {'permission': 'READ'}]
    mock_get_team_repos.return_value = mock_team_repos

    # Act + assert that the returned data is correct
    assert _get_team_repos_for_multiple_teams(
        team_data,
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {
        'team1': {
            RepoPermission('https://github.com/org/repo1', 'WRITE'),
            RepoPermission('https://github.com/org/repo2', 'READ'),
        },
    }

    # Assert that we did not retry because this was the happy path
    mock_get_team_repos.assert_called_once_with('test-org', 'https://api.github.com', 'test-token', 'team1')


@patch('cartography.intel.github.teams._get_team_repos')
@patch('cartography.intel.github.teams.sleep')
def test_get_team_repos_github_returns_none(mock_sleep, mock_get_team_repos):
    # Arrange
    team_data = [{'slug': 'team1', 'repositories': {'totalCount': 1}}]
    mock_team_repos = MagicMock()
    # Set up the condition where GitHub returns a None url and None edge as in #1334.
    mock_team_repos.nodes = [None]
    mock_team_repos.edges = [None]
    mock_get_team_repos.return_value = mock_team_repos

    # Assert we raise an exception
    with pytest.raises(RuntimeError):
        _get_team_repos_for_multiple_teams(
            team_data,
            'test-org',
            'https://api.github.com',
            'test-token',
        )

    # Assert that we retry and give up
    assert mock_get_team_repos.call_count == 5
    assert mock_sleep.call_count == 4
