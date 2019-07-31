from __future__ import absolute_import

from .basic import *
from .execute import *
from .fileio import *
from .deployment import *

# Load any additional plugin commands!
import os
from common import utils

thirdparty_commands = os.path.join(
    utils.path_ancestor(os.path.abspath(__file__), 4),
    'thirdparty_commands/'
)

thirdparty_command_files = []
for file_ in os.listdir(thirdparty_commands):

    if file_.endswith('.py') and not file_.startswith('_'):
        # Find any known thirdparty commands
        thirdparty_command_files.append(
            os.path.join(thirdparty_commands, file_)
        )

paths = os.environ.get('FLAUNCH_COMMANDS_PATH', '')
for path in paths.split(os.pathsep) + thirdparty_command_files:
    if os.path.isfile(path) and path.endswith('.py'):
        utils.load_from_source(os.path.abspath(path))
