from typing import Dict

from . import repos
from . import teams


RESOURCE_FUNCTIONS: Dict = {
    'teams': teams.sync_github_teams,
    'repos': repos.sync,
}
