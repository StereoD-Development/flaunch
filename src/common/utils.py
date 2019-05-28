"""
Build management utilities
"""

import re
import os
import sys
import json
import shlex
import platform
import subprocess
import logging

from . import log
from .platformdict import PlatformDict
from .abstract import _AbstractFLaunchData, FLaunchDataError

PY3 = sys.version_info[0] == 3
SYSTEM = platform.system()

if PY3:
    def _iter(it):
        return it.items()
else:
    def _iter(it):
        return it.iteritems()

class LaunchJson(_AbstractFLaunchData):
    """
    Basic tool for handling launch.json files
    """
    def __init__(self, package, path):
        try:
            with open(path, 'r') as f:
                data = PlatformDict(json.load(f))
        except Exception as e:
            logging.error(path + ' - invalid json file')
            raise FLaunchDataError(str(e))

        _AbstractFLaunchData.__init__(self, package, path, data)


    def requires(self):
        """
        :return: list[str] of required packages
        """
        return self['requires'] or []


    def extends(self):
        """
        :return: str of package this one extends
        """
        return self['extends'] or []


def path_ancestor(path, count):
    if count <= 0:
        return path
    return path_ancestor(os.path.dirname(path), count - 1)


def run_(command_and_args, custom_env = {}, verbose = False):
    """
    Execute the command provided
    """
    env = dict(os.environ, **custom_env)
    os.environ.update(env)

    if not isinstance(command_and_args, list):
        full_command = shlex.split(command_and_args)
    else:
        full_command = command_and_args

    for i, c in enumerate(full_command):
        if re.match("^\"[^\"]\"^", c):
            # Strip away surrounding the quotes
            full_command[i] = c[1:-1]

    logging.info("Running command: " + " ".join(full_command))

    if PY3:
        return subprocess.run(full_command)
    else:
        return subprocess.check_call(full_command)


def local_path(package, version=None, base_only=False):
    """
    Based on the package and the local version, build a
    path that we know will hold onto this version of the
    software suite
    :param pacakge: The package that we're localizing (str)
    :param version: The version of the pacakge (str)
    :param base_only: Should we only return the root of all apps
    :return: str
    """
    if platform.system() == 'Windows':
        base = os.path.join(os.environ['APPDATA'], 'flux_launch', 'apps')
    elif platform.system() == 'Linux':
        base = os.path.join(
            os.path.expanduser('~'),
            '.local',
            'share',
            'flux_launch',
            'apps'
        )

    if not os.path.isdir(base):
        os.makedirs(base)

    if base_only:
        return base

    if version is None:
        return os.path.join(base, package).replace('\\', '/')

    return os.path.join(base, package, version).replace('\\', '/')
