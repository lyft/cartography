from typing import Dict

from . import repos
from . import teams
from . import users


RESOURCE_FUNCTIONS: Dict = {
    'users': users.sync,
    'teams': teams.sync_github_teams,
    'repos': repos.sync,
}
