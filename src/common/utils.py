"""
Build management utilities
"""
from __future__ import absolute_import

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
    string_types = str
else:
    def _iter(it):
        return it.iteritems()
    string_types = (str, basestring)

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
        return self['extends'] or None


    def default_args(self):
        """
        :return: list of default arguments
        """
        return self['default_args'] or None


    def set_base(self, base_ljson):
        """
        :param base_ljson: The LaunchJson that this instance overrides
        :return: None
        """
        self._path = base_ljson._path
        self._data = PlatformDict(
            dict(merge_dicts(base_ljson._data.to_dict(), self._data.to_dict()))
        )


def path_ancestor(path, count):
    if count <= 0:
        return path
    return path_ancestor(os.path.dirname(path), count - 1)


def run_(command_and_args, custom_env = {}, verbose = False, build_file = None):
    """
    Execute the command provided
    :param command_and_args: list|str of the command and arguments we want to run
    :param custom_env: Environment values we want to utilize over our current environ
    :param verbose: Not used currently
    :param build_file: For building, this is a BuildFile instance that has additional
                       environment augmentation
    :return: int exit code
    """
    env = dict(os.environ, **custom_env)
    if build_file is not None:
        build_file.command_environment(env)
    os.environ.update(env)

    if not isinstance(command_and_args, (list, tuple)):
        full_command = shlex.split(command_and_args)
    else:
        full_command = list(command_and_args)

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


def add_metaclass(metaclass):
    """
    Taken from the six module. Python 2 and 3 compatible.
    """
    def wrapper(cls):
        """
        The actual wrapper. take the given class and return one that contains the proper metaclass.
        """
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper


def merge_dicts(dict1, dict2, combine_keys=None, ignore=None):
    '''
    Merge dictionaries recursively and pass back the result.
    If a conflict of types arrive, just get out with what
    we can.
    '''
    if combine_keys is None:
        combine_keys = {}
    if ignore is None:
        ignore = []
    def _merge_list_of_dicts(list1, list2, key):

        list1_values = [l[key] for l in list1]
        list2_values = [l[key] for l in list2]

        for v in set(list1_values).union(list2_values):
            if v in list2_values:
                # If the value is in the second list, we use that instead
                yield list2[list2_values.index(v)]
            else:
                yield list1[list1_values.index(v)]


    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                if k in ignore:
                    yield (k, dict2[k])
                else:
                    yield (k, dict(merge_dicts(dict1[k], dict2[k], combine_keys, ignore)))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.

                # That is, unless, we've supplied combine keys. This is for list
                # concatinaion based on a given key.
                if k in combine_keys:
                    if isinstance(dict1[k], list) and isinstance(dict2[k], list):
                        yield (k, list(_merge_list_of_dicts(dict1[k], dict2[k], combine_keys[k])))
                    else:
                        yield (k, dict2[k])
                else:
                    yield (k, dict2[k])
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])