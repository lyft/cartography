from typing import Dict

from . import members
from . import projects
from . import repositories


RESOURCE_FUNCTIONS: Dict = {
    'members': members.sync,
    'projects': projects.sync,
    'repositories': repositories.sync,
}
